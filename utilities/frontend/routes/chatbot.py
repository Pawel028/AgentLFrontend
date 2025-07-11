from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import os
import base64
from PIL import Image
import io
import uuid
import json
from threading import Thread

from utilities.backend.docrecognizer import AzureDocIntelligenceClient
from utilities.backend.doc_extracter_agent import extractorAgent
from utilities.backend.litigator_agent import lawyerAgent

chatbot_bp = Blueprint('chatbot', __name__)
doc_intelligence_client = AzureDocIntelligenceClient(
    endpoint=os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT'),
    key=os.getenv('DOCUMENTINTELLIGENCE_KEY')
)

# 🔁 Shared in-memory result store
result_store = {}

# ---------------------- ROUTE: /main ----------------------
@chatbot_bp.route('/main', methods=['GET', 'POST'])
def main():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    # session.setdefault('lawyer_response', "")
    # session.setdefault('chat_history', [])
    # session.setdefault('uploaded_Img_text', [])
    # session.setdefault('uploaded_Img_text_summary', [])

    if 'chat_history' not in session:
        session['chat_history'] = []
    chat_history = session['chat_history'] 

    if 'lawyer_response' not in session:
        session['lawyer_response'] = []
    # lawyer_response = session['lawyer_response'] 

    print('lawyer_response: ',session.setdefault('lawyer_response', ""))
    if 'generate_results' in request.form:
        orchestratorAgent_obj = lawyerAgent(
            chat_history=session['chat_history'],
            uploaded_Img_text=session['uploaded_Img_text'],
            uploaded_Img_text_summary=session['uploaded_Img_text_summary']
        )
        print(session['uploaded_Img_text_summary'])
        lawyer_response = orchestratorAgent_obj.finalize()
        lawyer_response1 = [session['lawyer_response']]
        lawyer_response1.append(lawyer_response)
        session['lawyer_response'] = lawyer_response1
        return redirect(url_for('chatbot.main'))

    if 'delete_history' in request.form:
        session['chat_history'] = []
        session['uploaded_Img_text'] = []
        session['uploaded_Img_text_summary'] = []
        session['lawyer_response'] = ""
        return redirect(url_for('chatbot.main'))

    if request.method == 'POST':
        user_msg = request.form.get('user_input')
        if user_msg:
            bot_msg = f"You said: {user_msg}"
            chat_history.append(("User", user_msg))
            chat_history.append(("Bot", bot_msg))
            session['chat_history'] = chat_history

    return render_template(
        'chatbot_main.html',
        chat_history=chat_history,
        lawyer_response=session.get('lawyer_response', "")
    )

# ---------------------- ROUTE: /click-doc ----------------------
@chatbot_bp.route('/click-doc', methods=['GET', 'POST'])
def click_doc():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        data_url = request.form.get('image_data')
        if data_url:
            header, encoded = data_url.split(",", 1)
            image_bytes = base64.b64decode(encoded)

            try:
                Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                return f"Invalid image: {e}"

            session_id = str(uuid.uuid4())
            session['job_id'] = session_id

            # 🔁 Background thread for doc processing
            thread = Thread(target=background_doc_process, args=(image_bytes, session_id))
            thread.start()

            return redirect(url_for('chatbot.click_doc'))

    return render_template('click_doc.html')

# ---------------------- BACKGROUND THREAD TO PREPARE RESULT ----------------------
def background_doc_process(image_bytes, session_id):
    print("📄 Running Azure Document Intelligence...")

    text = doc_intelligence_client.analyze_read(bytes_data1=image_bytes)
    result_json = json.dumps(text)

    extractorAgent_obj = extractorAgent(result_json)
    extracted_data = extractorAgent_obj.extract()

    result_store[session_id] = {
        "content": extracted_data.content,
        "summary": extracted_data.summary
    }

    print(f"[INFO] ✅ Result prepared for session: {session_id}")

# ---------------------- ROUTE: /process-doc ----------------------
@chatbot_bp.route('/process-doc', methods=['GET'])
def run_doc_intelligence():
    session_id = session.get('job_id')
    print(session)
    if not session_id:
        return jsonify({"status": "no_job"})

    # If the background thread has completed processing
    if session_id in result_store:
        result = result_store.pop(session_id, None)

        # Safely retrieve or initialize session lists
        # session.setdefault('uploaded_Img_text', [])
        # session.setdefault('uploaded_Img_text_summary', [])
        uploaded_text = session['uploaded_Img_text']
        uploaded_text_summary = session['uploaded_Img_text_summary']
        uploaded_text.append(result.get('content', ''))
        uploaded_text_summary.append(result.get('summary', ''))
        session['uploaded_Img_text'] = uploaded_text
        session['uploaded_Img_text_summary'] = uploaded_text_summary
        session['job_id'] = None
        print(f"[INFO] ✅ Result moved to session for {session_id}")
        print("📄 Summary:", session['uploaded_Img_text_summary'])

        return jsonify({
            "status": "done",
            "content": result.get('content', ''),
            "summary": result.get('summary', '')
        })

    # Still processing
    return jsonify({"status": "processing"})

# ---------------------- ROUTE: /get-uploaded-img-text ----------------------
@chatbot_bp.route('/get_uploaded_img_text', methods=['GET'])
def get_uploaded_img_text():
    text = session.get('uploaded_Img_text', [])
    return jsonify({"text": text})
