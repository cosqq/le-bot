from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
import string
import logging 
from LLM import LLM
import ray 
from utils import * 
import os
logger = logging.getLogger(__name__)

class Processer: 
    def __init__(self):
        self.model = LLM()

    async def handle_webhook(self, request:Request):
        data = await request.json()

        # Initialize Token headers.
        installation = data.get("installation")
        if installation and installation.get("id"):
            installation_id = installation.get("id")
            logger.info(f"Installation ID: {installation_id}")

            JWT_TOKEN = generate_git_jwt_token()
            
            installation_access_token = await get_installation_access_token(
                JWT_TOKEN, installation_id
            )

            headers = {
                "Authorization": f"Bearer {installation_access_token}",
                "User-Agent": "le-bot",
                "Accept": "application/vnd.github+json",
            }
        else:
            raise ValueError("No app installation found.")

        # Ensure PR exists and is opened
        if "pull_request" in data.keys() and ( data["action"] in ["created", "synchronize", "reopened"] ):
            pr = data.get("pull_request")
            pr_file_diff = await get_pr_file_diff(pr ,headers)

            processed_pr_file_diff = []
            for file in pr_file_diff.json(): 
                processed_pr_file_diff.append( {
                        "fileName" : file["filename"], 
                        "filePatch": file.get("patch", "")

                })

            print (processed_pr_file_diff)

        #                 content, model, prompt_tokens, completion_tokens = \
        #                     self.start_ray_inferencing(content=context_files) if ray.is_initialized() else self.model.mentor(content=context_files)

        return JSONResponse(content={}, status_code=200)


    def start_ray_inferencing(self, content):

        futures = [self.model.ray_mentor(content=v) for v in content.values()]
        suggestions = ray.get(futures)

        content = {k: v[0] for k, v in zip(content.keys(), suggestions)}
        models = (v[1] for v in suggestions)
        prompt_tokens = sum(v[2] for v in suggestions)
        completion_tokens = sum(v[3] for v in suggestions)
        print_content = ""
        for k, v in content.items():
            print_content += f"{k}:\n\t{v}\n\n"
            
        logger.info(print_content)

        # TODO: fix models function
        return print_content, models, prompt_tokens, completion_tokens

