from mistralai.models.chat_completion import ChatMessage
from mistralai.client import MistralClient
import ray
import logging

logger = logging.getLogger("ray")

@ray.remote
class LLM(object):
    def __init__(self, model_id, api_key):
        logger.info("LLM -----| Mistral LLM initialized")
        self.model_id = model_id
        self.api_key = api_key
    
    
    def mentor(self, prompt_content):


        logger.info("LLM -----| Prepraring Prompt template ...")
        system_message = ChatMessage(role='system', content=f"""As an expert in coding, I can provide you with guidance, best practices, and insights on a wide range of programming languages and technologies. 
                                    \n  I can help you write clean, efficient, and readable code, and offer suggestions to improve your overall code quality.
                                    \n  You main TASK is to Improve the CONTENT {prompt_content}.
                                    \n  To improve the CONTENT:
                                    \n  1. Criticise syntax, grammar, punctuation, style, etc.
                                    \n  2. Recommend common technical writing knowledge, such as used in Vale and the Google developer documentation style guide.
                                    \n  3. If the content is good, don't comment on it.
                                    \n  4. You can use GitHub-flavored markdown syntax in your answer."""
                                    )

        user_message = ChatMessage(role='user', content=f"""Improve this content.
                                                    \n Don't comment on file names or other meta data, just the actual text.
                                                    \n The {prompt_content} will be in JSON format and contains file name keys and text values. Make sure to give very concise feedback per file.
                                            """)
                                   
        messages = [system_message, user_message]

        logger.info("LLM -----| Setting up Mistral LLM clients")
        client = MistralClient(api_key=self.api_key)
        retrieved_job = client.jobs.retrieve(job_id=self.model_id)


        logger.info("LLM -----| Mistral LLM mentor is performing inferencing ...")
        chat_response = client.chat(
            model=retrieved_job.fine_tuned_model,
            messages=messages
        )

        logger.info("LLM -----| Mistral LLM mentor inferencing done, content returning ...")
        return {
            "chat_response":chat_response.choices[0].message.content, 
            "model_id":retrieved_job.fine_tuned_model , 
            "chat_prompt_tokens":chat_response.usage.prompt_tokens, 
            "chat_completion_tokens":chat_response.usage.completion_tokens,
            "full_chat_reponse":chat_response
        }