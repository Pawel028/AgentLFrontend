from langchain.chat_models.azure_openai import AzureChatOpenAI
# import openai
import os
from dotenv import load_dotenv, find_dotenv
import openai
from openai import OpenAI
from pydantic import BaseModel, ConfigDict,validator
from typing import Optional, List, Dict, Any
load_dotenv(find_dotenv())

openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_API_KEY")

class demographic_extractor_struct(BaseModel):
    Party_Identifier: List[Dict[str, Any]]
    completion_tokens: int
    prompt_tokens: int

class demographicextractorAgent():
    def __init__(self, chat_history:List, 
                uploaded_Img_text:List, 
                uploaded_Img_text_summary:List):
        self.chat_history = "\n".join(chat_history)
        self.uploaded_Img_text = "\n".join(uploaded_Img_text)
        self.uploaded_Img_text_summary = "\n".join(uploaded_Img_text_summary)

    def extract_Ids(self):        
        client = OpenAI()
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": "You are a helpful assistant designed to output JSON. You need to extract the Party demographic Identifications from the data."},
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self.uploaded_Img_text}
                    ]
                }
            ],
            response_format=demographic_extractor_struct
        )
        return response.choices[0].message.parsed
