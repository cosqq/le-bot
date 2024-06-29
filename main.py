import ray
import re, os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ray import serve
from utility.utils import extract_invalid_code_snippet
from constants import *
from utility.Processer import Processer


app = FastAPI()
processor =  Processer()

logger = logging.getLogger("ray")

try:
    ray.init() # good practice for production to write to logs and log_to_driver=False
except:
    logger.error("Ray init failed.")


@serve.deployment()
@serve.ingress(app)
class ApiServer:
    @app.get("/")
    async def read_root(self):
        return {"message": "le-bot is ready."}

    @app.post("/webhook")
    async def handle_webhook_route(self, request:Request) -> JSONResponse:
        return await processor.handle_webhook(request)
    
    # @app.get("/predict")
    # def mistral_inference(self) -> JSONResponse:

    #     logger.info(f"FASTAPI ---| Performing inferencing")
    #     mistral_output = ""

    #     try:
    #         logger.info("FASTAPI ---| Loading in processor environments")

    #         logger.info("FASTAPI ---| Preparing payload content for LLM")
    #         contents = [{'messages': [{'content': 'The following CODE SNIPPET contains a typo. Please identify the mistake but do not change the original structure:\n                                \n\nContent path: "doc/models.md"\n                                \nINVALID CODE SNIPPET:\n"`C(\'name\')` - a pipeline config option" ','role': 'user'},
    #                     {'content': 'The typo identified in the code snippet is: "- `C(\'name\')` - a pipeline config option"\n                                \n\nContent path: "doc/models.md"\n                                \nCORRECTED CODE SNIPPET:\n"- `C(\'name\')` - a pipeline config option" ','role': 'assistant'}]}]
    #         contents = [extract_invalid_code_snippet(i['messages'][0]['content']) for i in contents]

    #         logger.info("FASTAPI ---| Content is read and loaded for inferencing")
    #         mistral_output = processor.ray_mentor(prompt_contents=contents) # uncomment to run llm

    #     except Exception as e:
    #         logger.error(f"FASTAPI ---| Exception on inferencing{e}", )

    #     logger.info("FASTAPI ---| Inferencing completed")
    #     return {"results": mistral_output}



bot = ApiServer.bind()