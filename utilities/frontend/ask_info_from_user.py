from langchain.chat_models.azure_openai import AzureChatOpenAI
# import openai
import os
from dotenv import load_dotenv, find_dotenv
import openai
from openai import OpenAI
load_dotenv(find_dotenv())
from typing import Optional, List, Dict, Any

openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_version = "2022-12-01"
openai.api_key = os.getenv("OPENAI_API_KEY")

def AskInfo(query,chat_history):        
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": [
                    {"type": "text", "text": f'''You are an assistant whose task is to ask for more information from the user.
                    You will be given a query and you will ask the user to provide more information about the : {query}. You also have to figure
                    out if the information provided is enough using the chat history: {chat_history}. Once you think the information
                    is enough you will have to reply: "Thank you for the information, You can click on the Address Issue button."'''},
                ]
            }
        ],
        response_format={"type": "text"}     
    )
    return response.choices[0].message.content

from pydantic import BaseModel, ConfigDict
class Task_item(BaseModel):
    Task_Instruction: str
    Task_results: str
    model_config = ConfigDict(extra="forbid") 

class final_writeup(BaseModel):
    Heading: str
    Paragraph: str

class lawyer_response_structure(BaseModel):
    task_list: List[Task_item]
    final_writeup: List[final_writeup]



def format_lawyer_response(raw_data: bytes) -> str:
    client = OpenAI()

    response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": '''You are a helpful assistant designed to output JSON.
                        You have to arrange the given write up into list of Tasks and Task Instructions and a list of final write up
                         having heading and the paragraphs. Do not change anything in the write up, just arrange it into the required format.
                        here is the write up: ''' + raw_data.decode('utf-8')},
                    ]
                }
            ],
            response_format=lawyer_response_structure
        )
    parsed = response.choices[0].message.parsed
    json_serializable = parsed.model_dump() 
    return json_serializable