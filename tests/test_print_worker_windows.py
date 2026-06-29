import importlib.util
from pathlib import Path


def _load_worker_module():
    script = Path(__file__).parents[1] / "scripts" / "print_worker_windows.py"
    spec = importlib.util.spec_from_file_location("print_worker_windows", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_worker_auto_discovers_dynamic_local_api_port(monkeypatch):
    module = _load_worker_module()

    class Result:
        def __init__(self, stdout):
            self.stdout = stdout

    def fake_run(args, **_kwargs):
        if args[0] == "tasklist":
            return Result('"kanpai-api.exe","5144","Console","1","10,000 K"\n')
        if args[0] == "netstat":
            return Result(
                "  TCP    127.0.0.1:56013    0.0.0.0:0    LISTENING    5144\n"
                "  TCP    127.0.0.1:56045    0.0.0.0:0    LISTENING    9999\n"
            )
        return Result("")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(
        module,
        "get_json",
        lambda url: {"status": "ok"} if url == "http://127.0.0.1:56013/health" else {},
    )

    assert module.resolve_api_base_url({"api_base_url": "auto"}) == "http://127.0.0.1:56013"


def test_worker_keeps_fixed_api_base_url():
    module = _load_worker_module()

    assert module.resolve_api_base_url({"api_base_url": "http://127.0.0.1:8000"}) == "http://127.0.0.1:8000"


def test_ticket_job_prints_client_and_counter_copy_with_delay(monkeypatch):
    module = _load_worker_module()
    printed = []
    sleeps = []

    monkeypatch.setattr(module.time, "sleep", lambda seconds: sleeps.append(seconds))

    module.print_job_content(
        "CAJA",
        {"job_type": "TICKET", "content_snapshot": "SOMOS KANPAI\nTOTAL $100\n"},
        printer=lambda target, content: printed.append((target, content)),
    )

    assert len(printed) == 2
    assert printed[0][0] == "CAJA"
    assert "COPIA CLIENTE" in printed[0][1].splitlines()[0]
    assert "SOMOS KANPAI" in printed[0][1]
    assert "COPIA MOSTRADOR" in printed[1][1].splitlines()[0]
    assert "TOTAL $100" in printed[1][1]
    assert sleeps == [module.TICKET_COPY_DELAY_SECONDS]


def test_non_ticket_job_prints_single_copy_without_delay(monkeypatch):
    module = _load_worker_module()
    printed = []
    sleeps = []

    monkeypatch.setattr(module.time, "sleep", lambda seconds: sleeps.append(seconds))

    module.print_job_content(
        "BARRA",
        {"job_type": "COMANDA", "content_snapshot": "COMANDA\nMESA 1\n"},
        printer=lambda target, content: printed.append((target, content)),
    )

    assert printed == [("BARRA", "COMANDA\nMESA 1\n")]
    assert sleeps == []

def test_worker_auto_discovers_dynamic_port_from_startup_trace(tmp_path, monkeypatch):
    module = _load_worker_module()
    trace = tmp_path / "startup-trace.log"
    trace.write_text(
        "2026-06-27T14:00:00 KANPAI_API_PORT=61000\n"
        "2026-06-27T14:10:00 KANPAI_API_PORT=62198\n",
        encoding="utf-8",
    )

    seen_urls = []

    def fake_get_json(url):
        seen_urls.append(url)
        if url == "http://127.0.0.1:62198/health":
            return {"status": "ok"}
        raise RuntimeError("not ready")

    monkeypatch.setattr(module, "get_json", fake_get_json)

    assert module.resolve_api_base_url(
        {"api_base_url": "auto", "startup_trace_paths": [str(trace)]}
    ) == "http://127.0.0.1:62198"
    assert seen_urls == ["http://127.0.0.1:62198/health"]


def test_worker_trace_discovery_falls_back_to_netstat(monkeypatch):
    module = _load_worker_module()

    class Result:
        def __init__(self, stdout):
            self.stdout = stdout

    def fake_run(args, **_kwargs):
        if args[0] == "tasklist":
            return Result('"kanpai-api.exe","5144","Console","1","10,000 K"\n')
        if args[0] == "netstat":
            return Result("  TCP    127.0.0.1:56013    0.0.0.0:0    LISTENING    5144\n")
        return Result("")

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "_candidate_startup_trace_paths", lambda _config=None: [])
    monkeypatch.setattr(
        module,
        "get_json",
        lambda url: {"status": "ok"} if url == "http://127.0.0.1:56013/health" else {},
    )

    assert module.resolve_api_base_url({"api_base_url": "auto"}) == "http://127.0.0.1:56013"

