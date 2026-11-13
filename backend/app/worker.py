import asyncio, logging, os, socket
from typing import Any
import httpx
from app.main import SUPABASE_URL, SUPABASE_KEY, SERVICE_ROLE_KEY, _process_analysis_job
logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'))
log=logging.getLogger('papersignal.worker')
POLL_SECONDS=max(2,int(os.getenv('WORKER_POLL_SECONDS','5')))
LEASE_SECONDS=max(300,int(os.getenv('WORKER_LEASE_SECONDS','1200')))
WORKER_ID=os.getenv('WORKER_ID',socket.gethostname())
def headers():
 if not SERVICE_ROLE_KEY: raise RuntimeError('SUPABASE_SERVICE_ROLE_KEY is required')
 return {'apikey':SERVICE_ROLE_KEY,'Authorization':'Bearer '+SERVICE_ROLE_KEY,'Content-Type':'application/json'}
async def claim(client:httpx.AsyncClient)->dict[str,Any]|None:
 response=await client.post(SUPABASE_URL+'/rest/v1/rpc/claim_analysis_job',headers=headers(),json={'p_worker_id':WORKER_ID,'p_lease_seconds':LEASE_SECONDS})
 response.raise_for_status(); rows=response.json(); return rows[0] if isinstance(rows,list) and rows else None
async def run():
 if not SUPABASE_URL or not SUPABASE_KEY or not SERVICE_ROLE_KEY: raise RuntimeError('Supabase URL, publishable key and service role key are required')
 log.info('Worker started id=%s',WORKER_ID)
 async with httpx.AsyncClient(timeout=30) as client:
  while True:
   try:
    job=await claim(client)
    if not job: await asyncio.sleep(POLL_SECONDS); continue
    log.info('Claimed job=%s attempt=%s',job['id'],job['attempts'])
    await _process_analysis_job(str(job['paper_id']),str(job['id']),str(job['user_id']),SERVICE_ROLE_KEY)
   except asyncio.CancelledError: raise
   except Exception: log.exception('Worker loop failed'); await asyncio.sleep(POLL_SECONDS)
if __name__=='__main__': asyncio.run(run())
