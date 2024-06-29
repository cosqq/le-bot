import re 
import logging 
import httpx
import jwt
import time
from constants import *


logger = logging.getLogger("ray")

def extract_invalid_code_snippet(text):
    logger.info("APP UTILITY ---| utility to extract invalid code content")
    pattern = r'INVALID CODE SNIPPET:\n"(.*)"'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None

def generate_git_jwt_token():
    payload = {
        "iat": int(time.time()),
        "exp": int(time.time()) + (10 * 60),
        "iss": APP_ID,
    }

    if PRIVATE_KEY:        
        jwt_token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
        return jwt_token
    raise ValueError("PRIVATE_KEY not found.")


async def get_installation_access_token(token, installation_id):
    url = f"{GIT_API_URL}/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "le-bot",
        "Accept": "application/vnd.github.v3+json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers)
        return response.json()["token"]

async def get_pr_file_diff(pr, headers):
    original_url = pr.get("url")
    parts = original_url.split("/")
    owner, repo, pr_number = parts[-4], parts[-3], parts[-1]

    url  = f"{GIT_API_URL}/repos/{owner}/{repo}/pulls/{pr_number}/files"

    headers["Accept"] = "application/vnd.github.raw+json"

    async with httpx.AsyncClient() as client:   
        response = await client.get(url, headers=headers)
        return response

# Update PR with comments
async def post_pr_comment(pr, headers, llm_response):

    headers["Accept"] = "application/vnd.github.raw+json"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{pr['issue_url']}/comments",
            json={"body": llm_response},
            headers=headers,
        )
        return response