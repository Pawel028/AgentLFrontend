from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
import os
import base64
from PIL import Image
import io
import uuid
import json
from threading import Thread
from datetime import datetime
import requests
chatbot_bp = Blueprint('chatbot', __name__)
# container_name = os.getenv('BLOB_CONTAINER_NAME')
# 🔁 Shared in-memory result store
result_store = {}

def clean_string(byte_str):
    # byte_str = b'["chat-20250712-202142","chat-20250712-211204"]\n'
    clean_str = byte_str.decode('utf-8').strip()
    session_list = json.loads(clean_str)
    session_list.sort(reverse=True)  # Sort sessions in descending order
    return session_list

# ---------------------- ROUTE: /main ----------------------
@chatbot_bp.route('/main', methods=['GET', 'POST'])
def main():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

    user = session['user']

    # 🔁 Auto-assign session name if first time
    if 'current_session' not in session:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session['current_session'] = f"chat_{timestamp}"
    current_session = session['current_session']
    
    if 'new_session' in request.form:
        new_session_name = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        session['chat_history'] = []
        session['uploaded_Img_text'] = []
        session['uploaded_Img_text_summary'] = []
        session['lawyer_response'] = ""
        session['current_session'] = new_session_name

        print(f"[INFO] 🆕 New session created: {new_session_name}")
        return redirect(url_for('chatbot.main'))

    # 🧠 Get available session names from blob
    target_url = os.getenv('backend_url')+'/api/SessionList'
    payload = {
            "user_name": user,
            "session_id": current_session
    }   
    session_list = requests.post(target_url, json=payload)
    print(session_list.content)
    session_list = clean_string(session_list.content)
    # session_list = session_blob_client.list_sessions(user)
    print(session_list)
    
    if 'session_name' not in request.form:
        if 'save_session' in request.form:
            selected_session = current_session
            session_data = {
                'chat_history': session.get('chat_history', []),
                'uploaded_Img_text': session.get('uploaded_Img_text', []),
                'uploaded_Img_text_summary': session.get('uploaded_Img_text_summary', []),
                'lawyer_response': session.get('lawyer_response', "")
            }
            target_url = os.getenv('backend_url')+'/api/SaveSession'
            payload = {
                "user_name": user,
                "session_name": selected_session,
                "chat_history": session_data['chat_history'],
                "uploaded_Img_text": session_data['uploaded_Img_text'],
                "uploaded_Img_text_summary": session_data['uploaded_Img_text_summary']
            }
            response = requests.post(target_url, json=payload)
            print(response.content)
            if response.status_code == 200:
                print(f"[INFO] ✅ Session '{selected_session}' saved successfully.")
    # 🔄 Load or Save session
    if 'session_name' in request.form:
        selected_session = request.form['session_name']
        
        target_url = os.getenv('backend_url')+'/api/LoadSession'
        payload = {
            "user_name": user,
            "session_name": selected_session
        }
        response = requests.post(target_url, json=payload)
        print(response.content)
        # if response.status_code != 200:
        #     print(f"[ERROR] ❌ Failed to load session '{selected_session}': {response.text}")
        #     return redirect(url_for('chatbot.main'))
        
        print(f"[INFO] ✅ Session '{selected_session}' loaded successfully.")
        print(response.json())
        # chat_history, uploaded_text, uploaded_summary = session_blob_client.load_session_from_blob()
        session['chat_history'] = response.json()['chat_history']
        session['uploaded_Img_text'] = response.json()['uploaded_text']
        session['uploaded_Img_text_summary'] = response.json()['summary']
        session['lawyer_response'] = ""
        print(session['current_session'])
        session['current_session'] = selected_session
        print(session['current_session'])

        return redirect(url_for('chatbot.main'))

    # 🧼 Initialize session vars if missing
    session.setdefault('chat_history', [])
    session.setdefault('uploaded_Img_text', [])
    session.setdefault('uploaded_Img_text_summary', [])
    session.setdefault('lawyer_response', "")

    # 🧠 Trigger orchestrator
    if 'generate_results' in request.form:
        target_url = os.getenv('backend_url')+'/api/finalize'
        payload = {
            "chat_history": session['chat_history'],
            "uploaded_Img_text": session['uploaded_Img_text'],
            'uploaded_Img_text_summary': session['uploaded_Img_text_summary']
        }
        response = requests.post(target_url, json=payload)
        # print(response)
        print(response.content)
        lawyer_response = response.json()['lawyer_response']
        if isinstance(session['lawyer_response'], str):
            session['lawyer_response'] = []
        session['lawyer_response'].append(lawyer_response)
        return redirect(url_for('chatbot.main'))

    # ❌ Reset chat
    if 'delete_history' in request.form:
        session['chat_history'] = []
        session['uploaded_Img_text'] = []
        session['uploaded_Img_text_summary'] = []
        session['lawyer_response'] = ""
        return redirect(url_for('chatbot.main'))

    # 💬 Handle user message
    if request.method == 'POST':
        user_msg = request.form.get('user_input')
        if user_msg:
            chat_history = session.get('chat_history', [])
            chat_history.append(("User", user_msg))
            chat_history.append(("Bot", f"You said: {user_msg}"))
            session['chat_history'] = chat_history

    return render_template(
        'chatbot_main.html',
        chat_history=session['chat_history'],
        lawyer_response=session.get('lawyer_response', ""),
        session_list=session_list,
        current_session=current_session
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

            process_id = str(uuid.uuid4())
            session['job_id'] = process_id
            session_id = session['current_session']
            # 🔁 Background thread for doc processing
            thread = Thread(target=background_doc_process, args=(image_bytes, session_id, session.get('user'), process_id))
            thread.start()

            return redirect(url_for('chatbot.click_doc'))

    return render_template('click_doc.html')

# ---------------------- BACKGROUND THREAD TO PREPARE RESULT ----------------------



def background_doc_process(image_bytes, session_id, user_name, process_id):
    print("📄 Running Azure Document Intelligence...")
    
    img_b64 = base64.b64encode(image_bytes).decode('utf-8')  # convert to string
    target_url = os.getenv('backend_url')+'/api/uploadfile'
    payload = {
        "image_bytes": img_b64,
        "user_name": user_name,
        "session_id": session_id,
        "process_id": process_id
    }
    response = requests.post(target_url, json=payload)
    print(response.json())
