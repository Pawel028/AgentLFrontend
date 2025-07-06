from langchain.chat_models.azure_openai import AzureChatOpenAI
# import openai
import os
from dotenv import load_dotenv, find_dotenv
import openai
from openai import OpenAI
from pydantic import BaseModel, ConfigDict,validator
from typing import Optional, List, Dict, Any
import json
load_dotenv(find_dotenv())

openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_API_KEY")

class PartyIdentifierItem(BaseModel):
    name: str
    address: str
    dob: str
    phone: str
    email: str

    model_config = ConfigDict(extra="forbid")  # 👈 Required!

class demographic_extractor_struct(BaseModel):
    Party_Identifier: List[PartyIdentifierItem]
    completion_tokens: int
    prompt_tokens: int
    model_config = ConfigDict(extra="forbid")


class demographicextractorAgent():
    def __init__(self, chat_history:List, 
                uploaded_Img_text:List, 
                uploaded_Img_text_summary:List):
        
        
        self.chat_history = "\n".join([x[0] + ": " + x[1] for x in chat_history])
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
                        {"type": "text", "text": "You are a helpful assistant designed to output JSON. You need to extract the Demographic details of the people involved from the data. This could have Name, Adress, age/date of birth, phone number, email, etc. You need to extract the Party Identifier from the data and return it in the format specified."},
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
        parsed = response.choices[0].message.parsed
        json_serializable = parsed.model_dump()  # or parsed.dict()
        json_string = json.dumps(json_serializable)
        return json_serializable
