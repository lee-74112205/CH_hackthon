from flask import Flask, jsonify
from flask_cors import CORS
import os
import sys
from flask import send_from_directory
import threading

# 重要：讓 Python 知道可以找到其他模組
sys.path.append(os.path.dirname(__file__))

# 匯入自己分好的模組
from recorder import AudioRecorder
from speech_to_text_test import SpeechToText
from command_classifier_claude import CommandClassifier
from text_to_speech_test import ResponseSpeaker

# 初始化 Flask
app = Flask(__name__)
CORS(app)

# 初始化所有元件
recorder = AudioRecorder()
transcriber = SpeechToText()
classifier = CommandClassifier()
speaker = ResponseSpeaker()

is_audio_playing = False

def play_audio_in_thread(audio_path):
    global is_audio_playing
    is_audio_playing = True
    speaker.play_audio(audio_path)
    is_audio_playing = False

@app.route('/audio_status', methods=['GET'])
def audio_status():
    return jsonify({"playing": is_audio_playing})

@app.route("/process_audio", methods=["POST"])
def process_audio():
    try:
        print("\n🎙️ 聆聽中...")
        recorder.wait_for_speech()

        audio_file = recorder.record()

        transcript_text = transcriber.transcribe_file(audio_file)
        if not transcript_text:
            return jsonify({"reply": "⚠️ 語音辨識失敗！"})

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
            combined = [f"{desc}，{code}" for desc, code in zip(description_list, code_list)]
            response_text = "\n".join(combined)
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = "⚠️ 無法識別命令"

        # 生成語音檔案
        audio_path = speaker.text_to_speech(response_text)

        # ✅ 啟動新的執行緒播放語音
        if audio_path:
            threading.Thread(target=play_audio_in_thread, args=(audio_path,)).start()

        print("✅ 完成一次完整語音互動！")

        # ✅ 馬上回傳，不等待播放
        return jsonify({"reply": response_text})

    except Exception as e:
        print(f"❌ 發生錯誤：{str(e)}")
        return jsonify({"reply": f"❌ 發生錯誤：{str(e)}"}), 500

if __name__ == "__main__":
    print("🚀 啟動 Flask 語音互動伺服器...")
    app.run(host="0.0.0.0", port=5001, debug=True)
