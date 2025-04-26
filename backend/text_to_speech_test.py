import os
import json
import requests
from datetime import datetime
import pygame
from dotenv import load_dotenv
import base64
import boto3

# ✅ 加載環境變量（正確路徑）
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config', '.env'))
load_dotenv(env_path)

class ResponseSpeaker:
    def __init__(self):
        # 設置 AWS Polly 客戶端
        self.client = boto3.client(
            "polly",
            region_name="us-east-1",
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )

        self.voice_id = "Zhiyu"  # 中文女聲
        self.language_code = "cmn-CN"
        self.output_format = "mp3"

        pygame.mixer.init()

        # ✅ 設定 audio_output 資料夾為絕對路徑
        self.audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'audio_output'))
        os.makedirs(self.audio_dir, exist_ok=True)

    def text_to_speech(self, text):
        """將文本轉換為語音並保存為文件"""
        try:
            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat=self.output_format,
                VoiceId=self.voice_id,
                LanguageCode=self.language_code
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_file = os.path.join(self.audio_dir, f'speech_{timestamp}.mp3')

            with open(audio_file, 'wb') as out:
                out.write(response["AudioStream"].read())

            return audio_file

        except Exception as e:
            print(f"轉換語音時出錯: {str(e)}")
            return None

    def play_audio(self, audio_file):
        """播放音訊文件"""
        if audio_file and os.path.exists(audio_file):
            try:
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            except Exception as e:
                print(f"播放音訊時出錯: {str(e)}")
        else:
            print("音訊文件不存在或生成失敗")

    def process_history_file(self, file_path):
        """處理歷史記錄文件並播放對應的回應"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'movement_plan' in data:
                text = "\n".join(data['movement_plan']['說明'])
            elif 'response' in data:
                text = data['response']
            else:
                raise ValueError("不支援的文件格式")

            print(f"正在轉換文本為語音：\n{text}\n")

            audio_file = self.text_to_speech(text)
            if audio_file:
                print(f"開始播放語音...")
                self.play_audio(audio_file)
                print(f"語音播放完成！\n")

        except Exception as e:
            print(f"處理文件時出錯: {str(e)}")

def main():
    speaker = ResponseSpeaker()

    # ✅ 測試直接語音合成
    test_text = "你好，我是你的語音助理，很高興為你服務！"
    print(f"\n測試語音合成: {test_text}")
    audio_file = speaker.text_to_speech(test_text)
    if audio_file:
        print(f"語音文件已生成: {audio_file}")
        speaker.play_audio(audio_file)

    # ✅ 測試不同類型的歷史記錄文件（如果需要的話）
    # test_files = [
    #     'data/chat_history/chat_20250410_104002.json',
    #     'data/movement_history/movement_20250410_142131.json',
    #     'data/query_history/query_20250410_104646.json'
    # ]
    #
    # for file_path in test_files:
    #     abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), file_path))
    #     if os.path.exists(abs_path):
    #         print(f"\n處理文件: {file_path}")
    #         speaker.process_history_file(abs_path)
    #     else:
    #         print(f"文件不存在: {file_path}")

if __name__ == "__main__":
    main()
