from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ray import serve
from Processer import Processer

app = FastAPI()
processor =  Processer()
# processor.load_env()

@serve.deployment()
@serve.ingress(app)
class ApiServer:
    @app.get("/")
    async def read_root(self):
        return {"message": "le-bot is ready."}

    @app.post("/webhook")
    async def handle_webhook_route(self, request:Request) -> JSONResponse:
        return await processor.handle_webhook(request)
    
bot = ApiServer.bind()