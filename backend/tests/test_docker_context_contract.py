from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_dockerignore_keeps_backend_tests_and_workflow_contracts_available():
    ignored = {
        line.strip().rstrip("/")
        for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "backend/tests" not in ignored
    assert ".github" not in ignored
    assert "COPY backend/ /workspace/backend/" in dockerfile
    assert "COPY .github/workflows/ /workspace/.github/workflows/" in dockerfile
    assert "WORKDIR /workspace/backend" in dockerfile
    assert "COPY --from=test /tmp/papersignal-backend-tests-passed" in dockerfile
    assert "COPY backend/app/ /app/app/" in dockerfile
