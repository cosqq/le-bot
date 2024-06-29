from fastapi import Request
from fastapi.responses import JSONResponse
from models.LLM import LLM
import logging 
import ray 
import os

from utility.utils import *
import os

from mistralai.models.chat_completion import ChatMessage
from mistralai.client import MistralClient
from constants import * 
import ray
import logging

logger = logging.getLogger("ray")



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

            llm_response_formatted = str(llm_response_dict['chat_responses'])
            await post_pr_comment(pr, headers, llm_response_formatted)

        logger.info("PROCESSOR ----| Github content processed")
        return JSONResponse(content={}, status_code=200)


    def ray_mentor(self, prompt_contents):
        logger.info("PROCESSOR ----| handling github webhook request with ray mentor")

        # generate results
        logger.info("PROCESSOR ----| Mistral LLM is performing inferencing distributedly")

        results = []
        len_prompt_contents = 2 # len(prompt_contents)
        for i in range(0, len_prompt_contents -1, 3):
            prompt_formatted = f"Patch Information: {prompt_contents[i]['filePatch']}, content_path: {prompt_contents[i]['fileName'] }"
            result = mentor.remote(prompt_formatted)
            results.append(ray.get(result))

        # collate results
        logger.info("PROCESSOR ----| Processing Mistral LLM content returned")
        corrections_chat_response = "\n".join([f['chat_response'] for f in results])

        logger.info("PROCESSOR ----| Processing done, content returning ...")
        return {
            "chat_responses" : corrections_chat_response,
        }

@ray.remote
def mentor(prompt_content):
    # system_message = ChatMessage(role='system', 
    #                                 content=f"""As an expert in coding, I can provide you with guidance, best practices, and insights on a wide range of programming languages and technologies. 
    #                                 \n  I can help you write clean, efficient, and readable code, and offer suggestions to improve your overall code quality.
    #                                 \n  Your main TASK is to Improve the CONTENT.
    #                                 \n  1. Criticise syntax, grammar, punctuation, style, etc.
    #                                 \n  2. Recommend common technical writing knowledge, such as used in Vale and the Google developer documentation style guide.
    #                                 \n  3. If the content is good, don't comment on it. 
    #                                 \n The CONTENT is {prompt_content}"""
    #                             )

    user_message = ChatMessage(role='user', content=f"""Provide concise feedback on the PATCH from Github.

                                                \n Don't comment on file names or other meta data, just the actual text.
                                                \n The {prompt_content} will be in JSON format and contains file name keys and text values. 
                                        """)
                                
    messages = [user_message]

    logger.info("LLM -----| Setting up Mistral LLM clients")
    client = MistralClient(api_key=MISTRAL_API_KEY)

    retrieved_job = client.jobs.retrieve(job_id=MODEL_ID if MODEL_ID else "")

    logger.info("LLM -----| Mistral LLM mentor is performing inferencing ...")
    chat_response = client.chat(
        model=retrieved_job.fine_tuned_model,
        messages=messages
    )

    logger.info("LLM -----| Mistral LLM mentor inferencing done, content returning ...")
    return {
        "chat_response":chat_response.choices[0].message.content
    }