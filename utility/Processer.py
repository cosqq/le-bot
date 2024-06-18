from fastapi import Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from utility.constants import *
from models.LLM import LLM
import httpx, string, os
import logging 
import ray 


logger = logging.getLogger("ray")

class Processer: 
    def __init__(self):
        logger.info("PROCESSOR ----| Processor initialized")
        pass

    def load_env(self):
        logger.info("PROCESSOR ----| Secrets is loading")

        secret_path=SECRET_PATH
        load_dotenv(os.environ.get("SECRET_FILE_PATH")) if not secret_path else load_dotenv(secret_path)

        self.mistral_api_key = os.environ.get("MISTRAL_API_KEY", "")
        self.model_id = os.environ.get("JOB_ID")

        logger.info("PROCESSOR ----| Secrets is loaded")


    async def handle_webhook(self, request:Request):

        logger.info("PROCESSOR ----| handling github webhook request")
        data = await request.json()

        installation = data.get("installation")
        if installation and installation.get("id"):
            installation_id = installation.get("id")
            logger.info(f"Installation ID: {installation_id}")

            JWT_TOKEN = generate_git_jwt_token()
            
            installation_access_token = await get_installation_access_token(
                JWT_TOKEN, installation_id
            )

            headers = {
                "Authorization": f"token {installation_access_token}",
                "User-Agent": "le-bot",
                "Accept": "application/vnd.github+json",
            }
        else:
            raise ValueError("No app installation found.")

        # Ensure PR exists and is opened
        if "pull_request" in data.keys() and ( data["action"] in ["opened", "reopened"] ):
            pr = data.get("pull_request")   
            # greet user else 

        # Tagging the issue to the PR 
        if "issue" in data.keys() and data.get("action") in ["created", "edited"]:
            issue = data["issue"]
            if "/pull/" in issue["html_url"]:
                pr = issue.get("pull_request")

                comment = data.get("comment")
                comment_body = comment.get("body")
                # Remove all whitespace characters except for regular spaces
                comment_body = comment_body.translate(
                    str.maketrans("", "", string.whitespace.replace(" ", ""))
                )

                author_handle = comment["user"]["login"]
                if (
                    author_handle != "docu-mentor[bot]"
                    and "@docu-mentor run" in comment_body
                ):
                    async with httpx.AsyncClient() as client:
                        # Fetch diff from GitHub
                        files_to_keep = comment_body.replace(
                            "@docu-mentor run", ""
                        ).split(" ")
                        files_to_keep = [item for item in files_to_keep if item]

                        logger.info(files_to_keep)

                        url = get_diff_url(pr)
                        diff_response = await client.get(url, headers=headers)
                        diff = diff_response.text

                        files_with_lines = parse_diff_to_line_numbers(diff)

                        # Get head branch of the PR
                        headers["Accept"] = "application/vnd.github.full+json"
                        head_branch = await get_pr_head_branch(pr, headers)

                        # Get files from head branch
                        head_branch_files = await get_branch_files(pr, head_branch, headers)
                        print("HEAD FILES", head_branch_files)

                        # Enrich diff data with context from the head branch.
                        context_files = get_context_from_files(head_branch_files, files_with_lines)

                        # Filter the dictionary
                        if files_to_keep:
                            context_files = {
                                k: context_files[k]
                                for k in context_files
                                if any(sub in k for sub in files_to_keep)
                            }

                        content, model, prompt_tokens, completion_tokens = \
                            self.start_ray_inferencing(content=context_files) if ray.is_initialized() else self.model.mentor(content=context_files)

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

