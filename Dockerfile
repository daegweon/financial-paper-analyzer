# Railway deploys from the monorepo root, using this Dockerfile.
# Keep the backend test suite as a mandatory build dependency. This provides
# a deployment-time CI gate even when GitHub-hosted runners are unavailable.
FROM python:3.12-slim AS test
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
COPY backend/requirements-dev.txt /app/requirements-dev.txt
RUN pip install --no-cache-dir -r /app/requirements-dev.txt
COPY backend/app/ /app/app/
COPY backend/tests/ /app/tests/
COPY backend/pytest.ini /app/pytest.ini
COPY benchmark/ /benchmark/
RUN pytest -q && touch /tmp/papersignal-backend-tests-passed

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# This dependency forces BuildKit to execute the test stage before packaging
# the lean runtime image. pytest and test-only dependencies stay out of runtime.
COPY --from=test /tmp/papersignal-backend-tests-passed /tmp/papersignal-backend-tests-passed
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend/app/ /app/app/
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
