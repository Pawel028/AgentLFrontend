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
        
        print(type(chat_history))
        if type(chat_history)== str: 
            self.chat_history = chat_history
        else:
            self.chat_history = "\n".join([x[0] + ": " + x[1] for x in chat_history])
        if type(uploaded_Img_text)== str:
            self.uploaded_Img_text = uploaded_Img_text 
        else:
            self.uploaded_Img_text = [x[0] + ": " + x[1] for x in uploaded_Img_text]
        if type(uploaded_Img_text_summary)== str:
            self.uploaded_Img_text_summary = uploaded_Img_text_summary
        else:
            self.uploaded_Img_text_summary = [x[0] + ": " + x[1] for x in uploaded_Img_text_summary]

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
    

class OrchestratorItem(BaseModel):
    Step_id: int
    Instructions: str
    input_required: List[str]
    output_required: List[str]
    tools: Optional[List[str]] = None
    model_config = ConfigDict(extra="forbid")  # 👈 Required!

class Orchestrator_struct(BaseModel):
    Orchestrator: List[OrchestratorItem]
    completion_tokens: int
    prompt_tokens: int
    model_config = ConfigDict(extra="forbid")


class orchestratorAgent():
    def __init__(self, chat_history:List, 
                uploaded_Img_text:List, 
                uploaded_Img_text_summary:List):
        self.chat_history = "\n".join([x[0] + ": " + x[1] for x in chat_history])
        self.uploaded_Img_text = "\n".join(uploaded_Img_text)
        self.uploaded_Img_text_summary = "\n".join(uploaded_Img_text_summary)
        self.demographicextractorAgent_obj = demographicextractorAgent(
            chat_history=self.chat_history,
            uploaded_Img_text=self.uploaded_Img_text,
            uploaded_Img_text_summary=self.uploaded_Img_text_summary
        )
        self.Party_Id_data = self.demographicextractorAgent_obj.extract_Ids()
        

    def orchestrate(self):
        client = OpenAI()
        response = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": [
                        {"type": "text", "text": '''You are a helpful litigator and your task is to help the user. You need to provide 
                         an orchestration plan for the given Information. The plan should include what are the tasks a litigator needs
                         to do given the chat with user. You have to base you plan on the chat history, the uploaded image text,
                         the uploaded image text summary, and the Party Identifier data. You have to focus on solving the user Issue in the current instance.
                         The plan should be in JSON format with the following structure: 
                         Each step should have a unique Step_id, clear Instructions, input_required, output_required, and 
                         optional tools that can be used.'''},
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f'''Text in Image:{self.uploaded_Img_text} \n 
                         Summary of Text in Image: {self.uploaded_Img_text_summary} \n 
                         Chat History: {self.chat_history} \n 
                         Party Identifier Data: {self.Party_Id_data}'''}
                    ]
                }
            ],
            response_format=Orchestrator_struct
        )
        parsed = response.choices[0].message.parsed
        json_serializable = parsed.model_dump()  # or parsed.dict()
        json_string = json.dumps(json_serializable)
        return json_serializable
        
