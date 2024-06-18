from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
import string
import logging 
from LLM import LLM
import ray 
from dotenv import find_dotenv, load_dotenv
import os
logger = logging.getLogger(__name__)


### place holders to figure out 
# headers = {
#     "Authorization": f"token {installation_access_token}",
#     "User-Agent": "docu-mentor-bot",
#     "Accept": "application/vnd.github.VERSION.diff",
# }


class Processer: 
    def __init__(self):
        self.model = LLM()

    def load_env(self):
        print (os.environ.get("SECRET_FILE_PATH"))
        print (find_dotenv())
        load_dotenv(os.environ.get("SECRET_FILE_PATH"))
        print (os.environ.get("APP_ID"))

    async def handle_webhook(self, request:Request):
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

