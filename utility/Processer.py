from fastapi import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from utility.constants import *
from models.LLM import LLM
import httpx, string, os
import logging 
import ray 
<<<<<<< HEAD:utility/Processer.py


logger = logging.getLogger("ray")

=======
from utils import * 
import os
logger = logging.getLogger(__name__)

>>>>>>> 9be83e90d8764951e2aa384684c83dc5e4192d40:Processer.py
class Processer: 
    def __init__(self):
        logger.info("PROCESSOR ----| Processor initialized")
        pass

<<<<<<< HEAD:utility/Processer.py
    def load_env(self):
        logger.info("PROCESSOR ----| Secrets is loading")

        secret_path=SECRET_PATH
        load_dotenv(os.environ.get("SECRET_FILE_PATH")) if not secret_path else load_dotenv(secret_path)

        self.mistral_api_key = os.environ.get("MISTRAL_API_KEY", "")
        self.model_id = os.environ.get("JOB_ID")

        logger.info("PROCESSOR ----| Secrets is loaded")


=======
>>>>>>> 9be83e90d8764951e2aa384684c83dc5e4192d40:Processer.py
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

        #                 content, model, prompt_tokens, completion_tokens = \
        #                      self.start_ray_inferencing(content=context_files) if ray.is_initialized() else self.model.mentor(content=context_files)
            
            await post_pr_comment(pr, headers)

        logger.info("PROCESSOR ----| Github content processed")
        return JSONResponse(content={}, status_code=200)


    def ray_mentor(self, prompt_contents=None, git_pay_load=None,):
        logger.info("PROCESSOR ----| handling github webhook request with ray mentor")

        # intiialize LLM
        logger.info("PROCESSOR ----| Mistral LLM initialized")
        len_content = len(git_pay_load) if git_pay_load else 1
        llms = [LLM.remote(model_id=self.model_id, api_key=self.mistral_api_key) for i in range(len_content)] # init ray objects
        
        # generate results
            
        logger.info("PROCESSOR ----| Mistral LLM is performing inferencing distributedly")
        results = [llm.mentor.remote(prompt_content=prompt_contents[i]) for i, llm in enumerate(llms)] # run ray object functions 
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

