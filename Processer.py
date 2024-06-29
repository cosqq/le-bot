from fastapi import Request
from fastapi.responses import JSONResponse
import httpx

class Processer: 
    async def handle_webhook(self, request:Request):
        data = await request.json()

        # Ensure PR exists and is opened
        if "pull_request" in data.keys() and ( data["action"] in ["opened", "reopened"] ):
            pr = data.get("pull_request")   

            print (pr)
            
        return JSONResponse(content={}, status_code=200)
