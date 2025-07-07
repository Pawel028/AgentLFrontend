from flask import Blueprint, render_template, request, session, redirect, url_for
import os
from werkzeug.utils import secure_filename
import base64
from PIL import Image
import io
import uuid
import json
# from azure.core.serialization import serialize_model
from utilities.backend.docrecognizer import AzureDocIntelligenceClient
from utilities.backend.doc_extracter_agent import extractorAgent
from utilities.backend.litigator_agent import orchestratorAgent
chatbot_bp = Blueprint('chatbot', __name__)
doc_intelligence_client = AzureDocIntelligenceClient(endpoint = os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT'), key = os.getenv('DOCUMENTINTELLIGENCE_KEY'))

@chatbot_bp.route('/main', methods=['GET', 'POST'])
def main():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    if 'orchestrator_response' not in session:
        session['orchestrator_response'] = []  
    orchestrator_response = session['orchestrator_response']

    if 'generate_results' in request.form:
        orchestratorAgent_obj = orchestratorAgent(
            chat_history=session.get('chat_history', []),
            uploaded_Img_text=session.get('uploaded_Img_text', []),
            uploaded_Img_text_summary=session.get('uploaded_Img_text_summary', [])
        )
        orchestrator_response = orchestratorAgent_obj.orchestrate()
        print(orchestrator_response)
        session['orchestrator_response'] = orchestrator_response   
        return redirect(url_for('chatbot.main'))
    
    if 'delete_history' in request.form:
        session['chat_history'] = []
        session['uploaded_Img_text']= []
        session['uploaded_Img_text_summary']= []
        return redirect(url_for('chatbot.main'))

    if 'chat_history' not in session:
        session['chat_history'] = []
    chat_history = session['chat_history']
    
    if request.method == 'POST':
        if 'delete_history' in request.form:
            session['chat_history'] = []
        else:
            user_msg = request.form.get('user_input')
            if user_msg:
                bot_msg = f"You said: {user_msg}"
                chat_history.append(("User", user_msg))
                chat_history.append(("Bot", bot_msg))
                session['chat_history'] = chat_history
    
    uploaded_Img_text_summary = []
    if 'uploaded_Img_text_summary' in session:
        uploaded_Img_text_summary = session['uploaded_Img_text_summary']
    
    uploaded_Img_text = []
    if 'uploaded_Img_text' in session:
        uploaded_Img_text = session['uploaded_Img_text']

    return render_template('chatbot_main.html', chat_history=chat_history, uploaded_Img_text=orchestrator_response['Orchestrator'])

@chatbot_bp.route('/click-doc', methods=['GET', 'POST'])
def click_doc():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        data_url = request.form.get('image_data')

        if data_url:
            # Extract base64 string
            header, encoded = data_url.split(",", 1)
            image_bytes = base64.b64decode(encoded)

            # 🔍 OPTIONAL: Verify it's a valid image by loading it
            try:
                Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                return f"Image is invalid: {e}"

            # ✅ Call Azure with raw image bytes
            # try:
            text = doc_intelligence_client.analyze_read(
                bytes_data1=image_bytes,  # now raw bytes
            )
            # result_dict = serialize_model(text)
            print(type(text))            
            result_json = json.dumps(text)
            extractorAgent_obj = extractorAgent(result_json)
            extracted_data = extractorAgent_obj.extract()
            if 'uploaded_Img_text' not in session:
                session['uploaded_Img_text'] = []
            uploaded_Img_text = session['uploaded_Img_text']
            uploaded_Img_text.append(extracted_data.content)
            session['uploaded_Img_text'] = uploaded_Img_text

            if 'uploaded_Img_text_summary' not in session:
                session['uploaded_Img_text_summary'] = []
            uploaded_Img_text_summary = session['uploaded_Img_text_summary']
            uploaded_Img_text_summary.append(extracted_data.summary)
            session['uploaded_Img_text_summary'] = uploaded_Img_text_summary             
            return redirect(url_for('chatbot.click_doc'))
    return render_template('click_doc.html')