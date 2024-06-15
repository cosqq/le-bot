from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
import string
import logging 
from LLM import start_ray_inferencing, LLM

logger = logging.getLogger(__name__)
import ray 
from dotenv import load_dotenv

### place holders to figure out 
# headers = {
#     "Authorization": f"token {installation_access_token}",
#     "User-Agent": "docu-mentor-bot",
#     "Accept": "application/vnd.github.VERSION.diff",
# }


class Processer: 
    async def handle_webhook(self, request:Request):
        data = await request.json()
    
        # Ensure PR exists and is opened
        # # required env
        # load_dotenv('../conf/secrets.env')
        # model_id = os.environ.get("JOB_ID")
        # mistral_api_key = os.environ.get("MISTRAL_API_KEY")


        # # Get suggestions from Docu Mentor
        # content, model, prompt_tokens, completion_tokens = \
        #     start_ray_inferencing(content=context_files, model_id=model_id, mistral_api_key=mistral_api_key) if ray.is_initialized() else LLM(model_id=model_id, mistral_api_key=mistral_api_key).mentor(content=context_files)
            

        return JSONResponse(content={"data":data}, status_code=200)
