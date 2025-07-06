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
chatbot_bp = Blueprint('chatbot', __name__)
doc_intelligence_client = AzureDocIntelligenceClient(endpoint = os.getenv('DOCUMENTINTELLIGENCE_ENDPOINT'), key = os.getenv('DOCUMENTINTELLIGENCE_KEY'))

@chatbot_bp.route('/main', methods=['GET', 'POST'])
def main():
    if 'user' not in session:
        return redirect(url_for('auth.login'))

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

    # Get image filename
    image_preview = None
    if 'downsized_doc_image_filename' in session:
        image_preview = url_for('static', filename=f"static/uploads/{session['downsized_doc_image_filename']}")
        print(f"static/uploads/{session['downsized_doc_image_filename']}")
    return render_template('chatbot_main.html', chat_history=chat_history, image_preview=image_preview)


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
            print(f"Extracted Data: {extracted_data.content}")
            # except Exception as e:
            #     return f"Azure error: {e}"

            # # Optionally store the downsized image
            # downsized_image = image_bytes  # or your resized one
            # filename = f"{uuid.uuid4().hex}.jpg"
            # filepath = os.path.join("static", "uploads", filename)
            # os.makedirs(os.path.dirname(filepath), exist_ok=True)
            # with open(filepath, "wb") as f:
            #     f.write(downsized_image)

            # session['downsized_doc_image_filename'] = filename

            
            return redirect(url_for('chatbot.main'))

    return render_template('click_doc.html')


