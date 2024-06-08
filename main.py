from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ray import serve

import Processer

app = FastAPI()

@serve.deployment()
@serve.ingress(app)
class ApiServer:
    @app.get("/")
    async def read_root(self):
        return {"message": "le-bot is ready."}

    @app.post("/webhook/")
    async def handle_webhook_route(self, request:Request) -> None:
        return await Processer.handle_webhook(request)
    
bot = ApiServer.bind()