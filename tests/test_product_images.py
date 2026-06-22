from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import airtable.scripts.pull_airtable_to_sqlite as pull_module
from airtable.scripts.pull_airtable_to_sqlite import (
    TABLE_SPECS,
    apply_plan,
    build_remote_indexes,
    plan_records,
    prepare_records,
)
from app.core.database import Base
from app.core.config import get_settings
from app.main import app
from app.models import Product
from app.services.product_image_service import (
    ProductImageDownloadError,
    download_product_image,
)


class _ImageResponse:
    headers = {"Content-Type": "image/jpeg"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, _limit: int) -> bytes:
        return b"fake-png-content"


def _field_map() -> dict:
    import json

    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "airtable/schema/field_map.v1.json").read_text(encoding="utf-8-sig")
    )


def _empty_remote() -> dict[str, list[dict]]:
    return {spec.airtable_table: [] for spec in TABLE_SPECS}


def _product_record(attachment: list[dict]) -> dict:
    return {
        "id": "rec-product",
        "fields": {
            "sku": "yak coc poll",
            "tipo_producto": "Simple",
            "nombre": "Yakimeshi",
            "nombre_visible": "Yakimeshi con pollo",
            "precio_centavos": 15000,
            "multiplicador_receta_inventario": 1,
            "activo": True,
            "visible_pos": True,
            "Imagen_POS": attachment,
        },
    }


def test_product_image_url_resolves_local_media_and_keeps_legacy_compatible():
    product = Product(image_path="product-images/YAK-COC-POLL.png")
    assert product.image_url == "/media/product-images/YAK-COC-POLL.png"

    product.image_path = "/media/product-images/YAK-COC-POLL.png"
    assert product.image_url == "/media/product-images/YAK-COC-POLL.png"

    legacy_url = "https://v5.airtableusercontent.com/expired"
    product.image_path = legacy_url
    assert product.image_url == legacy_url

    product.image_path = None
    assert product.image_url is None


def test_product_image_static_endpoint_serves_image_content():
    image = get_settings().resolved_product_image_media_dir / "QA-PRODUCT.png"
    image.write_bytes(b"fake-png-content")
    try:
        response = TestClient(app).get("/media/product-images/QA-PRODUCT.png")
    finally:
        image.unlink(missing_ok=True)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"fake-png-content"


def test_download_product_attachment_saves_stable_local_file(tmp_path):
    attachment = {
        "url": "https://v5.airtableusercontent.com/fresh",
        "filename": "foto original.png",
        "type": "image/png",
    }

    image_path = download_product_image(
        attachment,
        sku="yak coc poll",
        media_dir=tmp_path,
        opener=lambda *_args, **_kwargs: _ImageResponse(),
    )

    assert image_path == "product-images/YAK-COC-POLL.png"
    assert (tmp_path / "YAK-COC-POLL.png").read_bytes() == b"fake-png-content"


def test_failed_attachment_download_warns_and_preserves_local_image(
    tmp_path, monkeypatch
):
    def fail_download(*_args, **_kwargs):
        raise ProductImageDownloadError("410 Gone")

    monkeypatch.setattr(pull_module, "download_product_image", fail_download)
    field_map = _field_map()
    remote = _empty_remote()
    remote["Productos"] = [
        _product_record(
            [
                {
                    "url": "https://v5.airtableusercontent.com/expired",
                    "filename": "foto.png",
                    "type": "image/png",
                }
            ]
        )
    ]
    indexes, index_issues = build_remote_indexes(remote, field_map)
    prepared, issues = prepare_records(
        remote,
        field_map,
        indexes,
        product_image_media_dir=tmp_path,
    )

    assert index_issues == []
    assert [(issue.level, issue.code) for issue in issues] == [
        ("warning", "product_image_download_failed")
    ]
    assert "image_path" not in prepared["Productos"][0].values

    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session, session.begin():
        session.add(
            Product(
                sku="yak coc poll",
                product_type="Simple",
                name="Nombre anterior",
                display_name="Nombre anterior",
                price_cents=100,
                active=True,
                visible_pos=True,
                image_path="product-images/YAK-COC-POLL.jpg",
            )
        )
    with Session(engine) as session:
        plan, planning_issues = plan_records(session, prepared, field_map)
        assert planning_issues == []
        apply_plan(session, plan, field_map)
        session.commit()
    with Session(engine) as session:
        saved = session.scalar(select(Product).where(Product.sku == "yak coc poll"))
        assert saved.image_path == "product-images/YAK-COC-POLL.jpg"
