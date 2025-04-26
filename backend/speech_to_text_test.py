import os
import json
import sys
import boto3
from dotenv import load_dotenv
from datetime import datetime

# ✅ 載入 config/.env（用絕對路徑避免錯誤）
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config', '.env'))
load_dotenv(env_path)

class SpeechToText:
    def __init__(self):
        # Whisper 模型配置
        self.endpoint_name = os.getenv('SAGEMAKER_ENDPOINT_NAME', 'jumpstart-dft-hf-asr-whisper-large-20250426-025518')
        self.region = os.getenv('AWS_REGION', 'us-west-2')

        # ✅ 創建 SageMaker 客戶端（加上明確金鑰）
        self.runtime = boto3.client(
            "sagemaker-runtime", 
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        # ✅ 設定儲存路徑為 backend/data/transcripts
        self.transcript_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'transcripts'))
        os.makedirs(self.transcript_dir, exist_ok=True)

    def save_transcript(self, transcript_text, audio_file_path, confidence=0.9):
        """保存转写结果"""
        audio_filename = os.path.basename(audio_file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        transcript_filename = os.path.join(self.transcript_dir, f"transcript_{timestamp}.json")

        data = {
            'audio_file': audio_filename,
            'timestamp': timestamp,
            'transcript': transcript_text,
            'confidence': confidence
        }

        with open(transcript_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"轉寫文本已保存至: {transcript_filename}")
        return transcript_filename

    def transcribe_file(self, audio_file_path):
        """將音頻文件轉換為文字"""
        print("開始轉換語音為文字...")

        try:
            with open(audio_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()

            response = self.runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType="audio/wav",
                Body=audio_bytes
            )

            response_body = response["Body"].read().decode("utf-8")
            result = json.loads(response_body)

            transcript_text = ""
            confidence = 0.9

            if "text" in result and isinstance(result["text"], list) and len(result["text"]) > 0:
                transcript_text = result["text"][0]
                confidence = result.get("confidence", 0.9)
                print(f"識別結果: {transcript_text}")

            print("語音轉換完成!")

            if transcript_text:
                self.save_transcript(transcript_text, audio_file_path, confidence)

            return transcript_text

        except Exception as e:
            print(f"轉換過程中出現錯誤: {str(e)}")
            return None

def main():
    # ✅ 測試音檔請放這個路徑（改為相對路徑，統一使用）
    test_audio_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'audio', 'test.wav'))

    print(f"開始測試語音識別，使用音頻文件：{test_audio_path}")

    if not os.path.exists(test_audio_path):
        print(f"錯誤：音頻文件不存在於路徑 {test_audio_path}")
        return

    speech_to_text = SpeechToText()
    transcript_text = speech_to_text.transcribe_file(test_audio_path)

    if transcript_text:
        print("\n識別結果摘要:")
        print(f"文本: {transcript_text}")
    else:
        print("未能獲取有效的識別結果")

if __name__ == "__main__":
    main()
