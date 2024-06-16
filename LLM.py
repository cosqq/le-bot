from mistralai.models.chat_completion import ChatMessage
from mistralai.client import MistralClient

import os
import ray
import logging


logger = logging.getLogger(__name__)

try:
    ray.init()
except:
    logger.info("Ray init failed.")

class LLM:
    def __init__(self):
        self.model_id = os.environ.get("JOB_ID")
        self.api_key = os.environ.get("MISTRAL_API_KEY", "")
    
    def mentor(self, content):
        system_message = ChatMessage(role='system', content=f"""As an expert in coding, I can provide you with guidance, best practices, and insights on a wide range of programming languages and technologies. 
                                    \n  I can help you write clean, efficient, and readable code, and offer suggestions to improve your overall code quality.
                                    \n  You main TASK is to Improve the CONTENT {content}.
                                    \n  To improve the CONTENT:
                                    \n  1. Criticise syntax, grammar, punctuation, style, etc.
                                    \n  2. Recommend common technical writing knowledge, such as used in Vale and the Google developer documentation style guide.
                                    \n  3. If the content is good, don't comment on it.
                                    \n  4. You can use GitHub-flavored markdown syntax in your answer."""
                                    )

        user_message = ChatMessage(role='user', content=f"""Improve this content.
                                                    \n Don't comment on file names or other meta data, just the actual text.
                                                    \n The {content} will be in JSON format and contains file name keys and text values. Make sure to give very concise feedback per file.
                                            """
                                    )
        messages = [system_message, user_message]
        retrieved_job = self.api_key.jobs.retrieve(job_id=self.model_id)
        chat_response = self.api_key.chat(
            model=retrieved_job.fine_tuned_model,
            messages=messages
        )

        return chat_response.choices[0].message.content, retrieved_job.fine_tuned_model , chat_response.usage.prompt_tokens, chat_response.usage.completion_tokens

    # @staticmethod
    @ray.remote
    def mentor_task(self, content):
        return self.mentor(content)

    # TODO: fix ray_mentor function
    def ray_mentor(self, content):
        futures = [
            self.mentor_task.remote(self, content)    
            for v in content.values()
            ]

        suggestions = ray.get(futures)
        content = {k: v[0] for k, v in zip(content.keys(), suggestions)}
        prompt_tokens = sum(v[2] for v in suggestions)
        completion_tokens = sum(v[3] for v in suggestions)

        print_content = ""
        for k, v in content.items():
            print_content += f"{k}:\n\t\{v}\n\n"
        logger.info(print_content)

        return print_content, self.model_id , prompt_tokens, completion_tokens
