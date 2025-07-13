from langchain.chat_models.azure_openai import AzureChatOpenAI
# import openai
import os
from dotenv import load_dotenv, find_dotenv
import openai
from openai import OpenAI
load_dotenv(find_dotenv())

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