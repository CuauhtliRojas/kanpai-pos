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
