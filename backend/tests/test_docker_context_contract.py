from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_dockerignore_keeps_complete_test_dependencies_in_build_context():
    ignored = {
        line.strip().rstrip("/")
        for line in (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "backend/tests" not in ignored
    assert ".github" not in ignored
    assert "learning" not in ignored
    assert "benchmark" not in ignored
    assert "supabase" not in ignored
    assert "COPY . /workspace/" in dockerfile
    assert "WORKDIR /workspace/backend" in dockerfile
    assert "PYTHONPATH=/workspace" in dockerfile
    assert "python scripts/smoke_candidate_http.py" in dockerfile
    assert "COPY --from=test /tmp/papersignal-backend-tests-passed" in dockerfile
    assert "COPY backend/app/ /app/app/" in dockerfile
