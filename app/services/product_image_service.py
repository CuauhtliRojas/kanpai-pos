"""Local, stable storage for Airtable product image attachments."""

from __future__ import annotations

import mimetypes
import re
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".webp"}
MAX_PRODUCT_IMAGE_BYTES = 20 * 1024 * 1024


class ProductImageDownloadError(RuntimeError):
    """An Airtable attachment could not be safely stored locally."""


def first_valid_attachment(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    for attachment in value:
        if not isinstance(attachment, dict):
            continue
        url = attachment.get("url")
        if isinstance(url, str) and urlparse(url.strip()).scheme in {"http", "https"}:
            return attachment
    return None


def stable_product_image_path(sku: str, attachment: dict[str, Any]) -> str:
    filename = str(attachment.get("filename") or "").strip()
    content_type = str(attachment.get("type") or "").partition(";")[0].strip()
    extension = _image_extension(filename, content_type)
    return f"product-images/{_safe_sku(sku)}{extension}"


def download_product_image(
    attachment: dict[str, Any],
    *,
    sku: str,
    media_dir: Path,
    opener: Callable[..., BinaryIO] = urlopen,
) -> str:
    """Download one attachment atomically and return its DB-relative path."""
    url = str(attachment.get("url") or "").strip()
    if urlparse(url).scheme not in {"http", "https"}:
        raise ProductImageDownloadError("attachment URL is missing or invalid")

    request = Request(url, headers={"User-Agent": "Kanpai-POS/1.0"})
    try:
        with opener(request, timeout=30) as response:
            response_type = str(response.headers.get("Content-Type") or "")
            response_type = response_type.partition(";")[0].strip().lower()
            if response_type and not response_type.startswith("image/"):
                raise ProductImageDownloadError(
                    f"unexpected attachment content type: {response_type}"
                )
            content = response.read(MAX_PRODUCT_IMAGE_BYTES + 1)
    except ProductImageDownloadError:
        raise
    except Exception as error:
        raise ProductImageDownloadError(str(error)) from error

    if not content:
        raise ProductImageDownloadError("attachment response was empty")
    if len(content) > MAX_PRODUCT_IMAGE_BYTES:
        raise ProductImageDownloadError("attachment exceeds 20 MiB limit")

    filename = str(attachment.get("filename") or "").strip()
    attachment_type = str(attachment.get("type") or "").partition(";")[0].strip()
    extension = _image_extension(filename, response_type or attachment_type)
    local_name = f"{_safe_sku(sku)}{extension}"
    media_dir.mkdir(parents=True, exist_ok=True)
    destination = media_dir / local_name
    temporary = media_dir / f".{local_name}.tmp"
    try:
        temporary.write_bytes(content)
        temporary.replace(destination)
    except OSError as error:
        temporary.unlink(missing_ok=True)
        raise ProductImageDownloadError(str(error)) from error
    return f"product-images/{local_name}"


def _safe_sku(sku: str) -> str:
    ascii_sku = unicodedata.normalize("NFKD", sku).encode("ascii", "ignore").decode()
    safe = re.sub(r"[^A-Z0-9]+", "-", ascii_sku.upper()).strip("-")
    if not safe:
        raise ProductImageDownloadError("SKU cannot produce a safe image filename")
    return safe


def _image_extension(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in ALLOWED_IMAGE_EXTENSIONS:
        return ".jpg" if suffix == ".jpeg" else suffix
    guessed = mimetypes.guess_extension(content_type.lower()) if content_type else None
    if guessed in ALLOWED_IMAGE_EXTENSIONS:
        return ".jpg" if guessed == ".jpeg" else guessed
    return ".jpg"
