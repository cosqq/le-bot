import re 
import logging 

logger = logging.getLogger("ray")

def extract_invalid_code_snippet(text):
    logger.info("APP UTILITY ---| utility to extract invalid code content")
    pattern = r'INVALID CODE SNIPPET:\n"(.*)"'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    else:
        return None