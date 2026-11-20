from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_dockerignore_keeps_backend_tests_available_to_the_build_stage():
    ignored = {
        line.strip().rstrip("/")
        for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "backend/tests" not in ignored
    assert (ROOT / "Dockerfile").read_text(encoding="utf-8").count(
        "COPY backend/tests/ /app/tests/"
    ) == 1
