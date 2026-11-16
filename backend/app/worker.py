import asyncio
import logging
import os
import socket
from typing import Any

import httpx

from app.main import (
    SERVICE_ROLE_KEY,
    SUPABASE_KEY,
    SUPABASE_URL,
    _process_analysis_job,
)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
log = logging.getLogger("papersignal.worker")
POLL_SECONDS = max(2, int(os.getenv("WORKER_POLL_SECONDS", "5")))
LEASE_SECONDS = max(300, int(os.getenv("WORKER_LEASE_SECONDS", "1200")))
HEARTBEAT_SECONDS = max(30, LEASE_SECONDS // 3)
WORKER_ID = os.getenv("WORKER_ID", socket.gethostname())


def headers() -> dict[str, str]:
    if not SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required.")
    if SERVICE_ROLE_KEY.startswith("sb_secret_"):
        # New Supabase secret keys are opaque API keys, never JWT bearer tokens.
        return {
            "apikey": SERVICE_ROLE_KEY,
            "Content-Type": "application/json",
        }
    if not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_PUBLISHABLE_KEY is required for legacy service_role keys.")
    # Backward compatibility for the legacy JWT-based service_role key.
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SERVICE_ROLE_KEY,
        "Content-Type": "application/json",
    }


async def claim(client: httpx.AsyncClient) -> dict[str, Any] | None:
    response = await client.post(
        SUPABASE_URL + "/rest/v1/rpc/claim_analysis_job",
        headers=headers(),
        json={"p_worker_id": WORKER_ID, "p_lease_seconds": LEASE_SECONDS},
    )
    response.raise_for_status()
    rows = response.json()
    return rows[0] if isinstance(rows, list) and rows else None


async def renew_lease(client: httpx.AsyncClient, job_id: str) -> bool:
    response = await client.post(
        SUPABASE_URL + "/rest/v1/rpc/renew_analysis_job_lease",
        headers=headers(),
        json={
            "p_job_id": job_id,
            "p_worker_id": WORKER_ID,
            "p_lease_seconds": LEASE_SECONDS,
        },
    )
    response.raise_for_status()
    return response.json() is True


async def schedule_retry(client: httpx.AsyncClient, job_id: str) -> bool:
    response = await client.post(
        SUPABASE_URL + "/rest/v1/rpc/schedule_failed_analysis_job_retry",
        headers=headers(),
        json={"p_job_id": job_id, "p_worker_id": WORKER_ID},
    )
    response.raise_for_status()
    return response.json() is True


async def keep_lease(
    client: httpx.AsyncClient,
    job_id: str,
    stop: asyncio.Event,
    lease_lost: asyncio.Event,
) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=HEARTBEAT_SECONDS)
            return
        except asyncio.TimeoutError:
            pass
        try:
            renewed = await renew_lease(client, job_id)
        except Exception:
            log.exception("Lease heartbeat failed job_id=%s", job_id)
            lease_lost.set()
            return
        if not renewed:
            log.error("Worker no longer owns lease job_id=%s", job_id)
            lease_lost.set()
            return


async def process_job(client: httpx.AsyncClient, job: dict[str, Any]) -> None:
    job_id = str(job["id"])
    stop = asyncio.Event()
    lease_lost = asyncio.Event()
    heartbeat = asyncio.create_task(keep_lease(client, job_id, stop, lease_lost))
    processing = asyncio.create_task(
        _process_analysis_job(
            str(job["paper_id"]),
            job_id,
            str(job["user_id"]),
            SERVICE_ROLE_KEY,
        )
    )
    try:
        while not processing.done():
            if lease_lost.is_set():
                processing.cancel()
                raise RuntimeError("Worker lease was lost; analysis was cancelled.")
            await asyncio.sleep(1)
        await processing
    finally:
        stop.set()
        await heartbeat
        if not processing.done():
            processing.cancel()
            try:
                await processing
            except asyncio.CancelledError:
                pass

    if await schedule_retry(client, job_id):
        log.warning("Failed job scheduled for retry job_id=%s", job_id)


async def run() -> None:
    if not SUPABASE_URL or not SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required.")
    if not SERVICE_ROLE_KEY.startswith("sb_secret_") and not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_PUBLISHABLE_KEY is required for legacy service_role keys.")
    log.info(
        "Worker started id=%s poll=%ss lease=%ss",
        WORKER_ID,
        POLL_SECONDS,
        LEASE_SECONDS,
    )
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            try:
                job = await claim(client)
                if not job:
                    await asyncio.sleep(POLL_SECONDS)
                    continue
                log.info(
                    "Claimed job_id=%s paper_id=%s attempt=%s job_created_at=%s",
                    job["id"],
                    job["paper_id"],
                    job["attempts"],
                    job.get("created_at") or "-",
                )
                await process_job(client, job)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("Worker loop failed")
                await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    asyncio.run(run())
