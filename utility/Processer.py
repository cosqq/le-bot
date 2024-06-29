from fastapi import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from utility.constants import *
from models.LLM import LLM
import httpx, string, os
import logging 
import ray 
from utils import * 
import os
logger = logging.getLogger(__name__)

class Processer: 
    def __init__(self):
        logger.info("PROCESSOR ----| Processor initialized")
        pass

    async def handle_webhook(self, request:Request):

        logger.info("PROCESSOR ----| handling github webhook request")
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
        if "pull_request" in data.keys() and ( data["action"] in ["created","opened", "synchronize", "reopened"] ):
            pr = data.get("pull_request")
            pr_file_diff = await get_pr_file_diff(pr ,headers)

            processed_pr_file_diff = []
            for file in pr_file_diff.json(): 
                processed_pr_file_diff.append( {
                        "fileName" : file["filename"], 
                        "filePatch": file.get("patch", "")

                })

            
            llm_response_dict= self.ray_mentor(prompt_contents=processed_pr_file_diff)

            print(llm_response_dict['chat_responses'])
            await post_pr_comment(pr, headers, llm_response_dict['chat_responses'])

        logger.info("PROCESSOR ----| Github content processed")
        return JSONResponse(content={}, status_code=200)


    def ray_mentor(self, prompt_contents=None):
        logger.info("PROCESSOR ----| handling github webhook request with ray mentor")

        # intiialize LLM
        logger.info("PROCESSOR ----| Mistral LLM initialized")
        len_content = len(prompt_contents)
        llms = [LLM.remote(model_id=MODEL_ID, api_key=MISTRAL_API_KEY) for i in range(len_content)] # init ray objects
        
        # generate results
        logger.info("PROCESSOR ----| Mistral LLM is performing inferencing distributedly")
        
        results = [llm.mentor.remote(prompt_content=f"""
                                   Path Information: { prompt_contents[i]['filePatch']}, content_path: {prompt_contents[i]['fileName'] }                   
                                    """) for i, llm in enumerate(llms)] # run ray object functions 
        futures = [ray.get(r) for r in results]

        # collate results
        logger.info("PROCESSOR ----| Processing Mistral LLM content returned")
        corrections_chat_response = "\n".join([f['chat_response'] for f in futures])
        prompt_tokens = sum(f['chat_prompt_tokens'] for f in futures)
        completion_tokens = sum(f['chat_completion_tokens'] for f in futures)
        model_id = futures[0]['model_id']

        logger.info("PROCESSOR ----| Processing done, content returning ...")
        return {
            "chat_responses" :corrections_chat_response,
            "model_id":model_id,
            "total_prompt_tokens_used":prompt_tokens,
            "total_completion_tokens_used":completion_tokens
        }

