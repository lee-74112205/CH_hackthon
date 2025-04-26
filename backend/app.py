# ===== 新版 app.py =====

import os
import threading
import time
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from recorder import AudioRecorder
from speech_to_text_test import SpeechToText
from text_to_speech_test import ResponseSpeaker
from command_classifier_claude import CommandClassifier
from flask_cors import CORS

# 載入環境變數
load_dotenv(os.path.join(os.path.dirname(__file__), 'config', '.env'))

app = Flask(__name__)
CORS(app)  # ✅ 開啟全域 CORS 支援

# 初始化主要元件
recorder = AudioRecorder()
transcriber = SpeechToText()
speaker = ResponseSpeaker()
classifier = CommandClassifier()

# ====== 持續監聽控制參數 ======
listening_thread = None
stop_listening = False
cur_state = "idle"
latest_response_text = ""
has_new_response = False
# ====== 核心功能 ======


def handle_heard_audio(audio_path):
    global cur_state, stop_listening, latest_response_text, has_new_response

    if stop_listening:
        return
    
    transcript_text = transcriber.transcribe_file(audio_path)
    if not transcript_text:
        return

    if process_command(transcript_text):
        return
    if speaker.check_audio():
        return
    
    cur_state = "thinking"
    command_type = classifier.classify_command(transcript_text)

    response = ""
    if command_type == '聊天':
        response = classifier.chat_with_gemini(transcript_text)
        classifier.save_chat_history(transcript_text, response, command_type)
    elif command_type == '查詢':
        response = classifier.handle_query(transcript_text)
        classifier.save_query_history(transcript_text, response, command_type)
    elif command_type == '行動':
        response = classifier.handle_movement(transcript_text)
        classifier.save_movement_history(transcript_text, response, command_type)

    if command_type == "行動" and isinstance(response, dict) and "說明" in response and "動作順序" in response:
        description_list = response["說明"]
        code_list = response["動作順序"]
        combined = [f"{code}，{desc}" for code, desc in zip(code_list, description_list)]
        response_text = "\n".join(combined)
    elif isinstance(response, str):
        response_text = response
    else:
        response_text = "⚠️ 無法識別命令"

    speaker.speak(response_text)
    cur_state = "talking"

    latest_response_text = response_text
    has_new_response = True


    

def process_command(text):
    """根據語音指令調整朗讀速度或中斷朗讀"""
    global cur_state
    if "停" in text:
        speaker.stop_audio()
        cur_state = "idle"
        return True
    elif "慢一點" in text:
        speaker.set_rate("80%")
        return True
    elif "快一點" in text:
        speaker.set_rate("130%")
        return True
    elif "正常" in text or "恢復正常" in text:
        speaker.set_rate("100%")
        return True
    else:
        return False
    

def listen_forever():
    global cur_state,stop_listening
    stop_listening = False

    def on_frame_captured(audio_path):
        global cur_state
        if(cur_state == "talking" and speaker.check_audio() == False):
            cur_state = "idle"
        handle_heard_audio(audio_path)

    recorder.listen_forever(on_heard_callback=on_frame_captured)

# ====== API ======

@app.route('/process_audio', methods=['POST'])
def process_audio():
    global listening_thread, stop_listening
    try:
        if listening_thread and listening_thread.is_alive():
            return jsonify({"message": "Already listening."})

        stop_listening = False
        listening_thread = threading.Thread(target=listen_forever)
        listening_thread.start()

        return jsonify({"message": "Listening started."})

    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")
        return jsonify({"reply": "❌ 錯誤: " + str(e)}), 500


# @app.route('/start_listen_forever', methods=['POST'])
# def start_listen_forever():
#     global listening_thread, stop_listening
#     if listening_thread and listening_thread.is_alive():
#         return jsonify({"message": "Already listening."})

#     stop_listening = False
#     listening_thread = threading.Thread(target=listen_forever)
#     listening_thread.start()

#     return jsonify({"message": "Listening started."})

# @app.route('/stop_listen_forever', methods=['POST'])
# def stop_listen_forever():
#     global stop_listening
#     stop_listening = True
#     return jsonify({"message": "Listening stopped."})

cunt = 0
@app.route('/audio_status', methods=['GET'])
def audio_status():
    global cur_state,cunt, latest_response_text, has_new_response

    if cur_state == "talking" and speaker.check_audio() == False:
        cur_state = "idle"

    response = {
        "state": cur_state,
        "has_new": has_new_response,
        "reply": latest_response_text
    }
    has_new_response = False
    latest_response_text = ""
    return jsonify(response)

if __name__ == '__main__':
    #listen_forever()
    app.run(host='0.0.0.0', port=5001, debug=True)
    
