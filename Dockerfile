# Railway deploys from the monorepo root, using this Dockerfile.
# Run the complete backend contract suite and a local HTTP/auth smoke in test stage.
# The runtime image below stays lean and never includes tests or research assets.
FROM python:3.12-slim AS test
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/workspace
WORKDIR /workspace
COPY . /workspace/
RUN pip install --no-cache-dir -r /workspace/backend/requirements-dev.txt
WORKDIR /workspace/backend
RUN pytest -q && python scripts/smoke_candidate_http.py && touch /tmp/papersignal-backend-tests-passed

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# This dependency forces BuildKit to execute the full test stage before
# packaging the lean runtime image. pytest and test-only dependencies stay out.
COPY --from=test /tmp/papersignal-backend-tests-passed /tmp/papersignal-backend-tests-passed
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend/app/ /app/app/
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
