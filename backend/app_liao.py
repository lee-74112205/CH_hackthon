import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import time
import boto3
import json
import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

print("🚀 啟動 Flask 伺服器...") 

# 載入 .env
load_dotenv()

app = Flask(__name__)
CORS(app)  # 開放跨域，讓前端能請求

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        # ---------- Step 1: 錄音 ----------
        fs = 16000  # 16kHz
        silence_threshold = 0.001
        silence_duration = 3

        print("🎙️ 開始錄音，請開始說話...")

        recording = []
        last_voice_time = time.time()
        block_duration = 0.5
        block_size = int(block_duration * fs)

        while True:
            block = sd.rec(block_size, samplerate=fs, channels=1, dtype='float32')
            sd.wait()
            energy = np.linalg.norm(block) / block_size
            recording.append(block)
            if energy > silence_threshold:
                last_voice_time = time.time()
            if time.time() - last_voice_time > silence_duration:
                print("⏹️ 偵測到3秒無聲，自動停止錄音")
                break

        recording = np.concatenate(recording, axis=0)
        write("demo.wav", fs, (recording * 32767).astype(np.int16))
        print("✅ 錄音完成，已儲存為 demo.wav")

        # ---------- Step 2: Speech-to-Text ----------
        print("🛜 傳送到 Whisper 辨識文字...")

        endpoint_name = "jumpstart-dft-hf-asr-whisper-large-20250426-025518"
        region = "us-west-2"
        runtime = boto3.client("sagemaker-runtime", region_name=region)

        with open("demo.wav", "rb") as f:
            audio_bytes = f.read()

        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="audio/wav",
            Body=audio_bytes
        )

        response_body = response["Body"].read().decode("utf-8")
        result = json.loads(response_body)

        if "text" in result and isinstance(result["text"], list):
            recognized_text = result["text"][0]
            print("🗣️ 辨識結果：", recognized_text)
        else:
            return jsonify({"reply": "⚠️ 語音辨識失敗！"})

        # ---------- Step 3: 呼叫 Claude 模型 ----------
        print("🤖 呼叫 Claude 模型分析內容...")

        bedrock = boto3.client(service_name="bedrock-runtime", region_name=region)

        body = json.dumps({
            "max_tokens": 512,
            "messages": [
                {
                    "role": "user",
                    "content": f"""
你是一個語音對話助手，請依照以下邏輯判斷使用者訊息的任務類型，並回答相應內容。

請將訊息分類為以下三種類型之一：「聊天」、「查詢」、「行動」。
回答時請務必在開頭標註分類結果，例如：「任務類型：聊天」。
其餘部分請自然地用中文回應使用者的問題或請求。

---（略，規則可以再根據需要補齊）---

以下是使用者訊息：

{recognized_text}
"""
                }
            ],
            "anthropic_version": "bedrock-2023-05-31"
        })

        model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        response = bedrock.invoke_model(
            body=body,
            modelId=model_id,
            contentType="application/json"
        )

        response_body = json.loads(response["body"].read())
        reply_text = response_body["content"][0]["text"]
        print("📝 Claude 回應：", reply_text)

        # ---------- Step 4: Text-to-Speech ----------
        print("🔊 使用 Polly 將回應轉語音...")

        polly = boto3.client("polly", region_name=region)

        response = polly.synthesize_speech(
            Text=reply_text,
            OutputFormat="mp3",
            VoiceId="Zhiyu",
            LanguageCode="cmn-CN"
        )

        with open("output.mp3", "wb") as f:
            f.write(response["AudioStream"].read())

        print("✅ 成功產生回應語音 output.mp3！")

        return jsonify({"reply": reply_text})

    except Exception as e:
        print("❌ 發生錯誤：", str(e))
        return jsonify({"reply": "❌ 發生錯誤：" + str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
