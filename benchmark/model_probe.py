"""One-shot synthetic provider liveness check. No PDF or customer content."""
import asyncio
import json
import os
import time
import httpx

async def main():
    key=os.getenv("GEMINI_API_KEY","")
    models=list(dict.fromkeys(x for x in (os.getenv("GEMINI_MODEL",""),os.getenv("GEMINI_FALLBACK_MODEL","")) if x))
    if not key or not models or os.getenv("FULL_AB_ALLOW_MODEL_CALLS")!="1":
        raise RuntimeError("Missing explicitly authorized benchmark provider configuration")
    out=[]
    async with httpx.AsyncClient(timeout=httpx.Timeout(connect=10,read=30,write=10,pool=10)) as client:
        for model in models:
            url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            payload={"contents":[{"role":"user","parts":[{"text":"Respond with a JSON object {\"ok\":true}. This is a synthetic API health test."}]}],
              "generationConfig":{"responseMimeType":"application/json",
                "responseJsonSchema":{"type":"object","properties":{"ok":{"type":"boolean"}},"required":["ok"],"additionalProperties":False},"maxOutputTokens":256}}
            start=time.perf_counter()
            item={"model":model}
            try:
                r=await client.post(url,headers={"x-goog-api-key":key,"Content-Type":"application/json"},json=payload)
                item["http_status"]=r.status_code
                if r.is_success:
                    data=r.json()
                    item["usage"]=data.get("usageMetadata",{})
                    item["finish_reason"]=((data.get("candidates")or[{}])[0]).get("finishReason")
                else:
                    try:
                        err=r.json().get("error",{})
                        item["provider_error_status"]=err.get("status")
                        item["provider_error_code"]=err.get("code")
                    except (ValueError,TypeError):
                        item["provider_error_status"]="unparsed"
            except Exception as exc:
                item["transport_error_type"]=type(exc).__name__
            item["wall_seconds"]=round(time.perf_counter()-start,4)
            out.append(item)
            print(json.dumps({"event":"provider_probe",**item}),flush=True)
    print(json.dumps({"event":"provider_probe_summary","results":len(out),
                      "successful":sum(x.get("http_status")==200 for x in out)}),flush=True)

if __name__=="__main__":
    asyncio.run(main())
