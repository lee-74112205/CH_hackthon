import os
import io
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
        self.current_rate = "100%"

        pygame.mixer.init()

        # ✅ 設定 audio_output 資料夾為絕對路徑
        self.audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'audio_output'))
        os.makedirs(self.audio_dir, exist_ok=True)

    def set_rate(self, rate):
        """設定播放速度"""
        self.current_rate = rate
        print(f"🎚️ 已設定播放速度為：{rate}")

    
    def speak(self, text):
        """用 Polly 直接朗讀文字，不存檔"""
        if not text:
            print("⚠️ 沒有文字內容，跳過朗讀")
            return
        try:
            ssml_text = f'<speak><prosody rate="{self.current_rate}">{text}</prosody></speak>'
            response = self.client.synthesize_speech(
                Text=ssml_text,
                OutputFormat=self.output_format,
                VoiceId=self.voice_id,
                LanguageCode=self.language_code,
                TextType="ssml"
            )
            audio_stream = response["AudioStream"].read()
            pygame.mixer.music.load(io.BytesIO(audio_stream))
            pygame.mixer.music.play()
            print(f"🔊 Polly 開始朗讀（語速 {self.current_rate}）：{text}")
        except Exception as e:
            print(f"⚠️ Polly 語音合成錯誤：{e}")

    def stop_audio(self):
        """中止音訊播放"""
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            print("音訊播放已中止")

    def check_audio(self):
        return pygame.mixer.music.get_busy()

def main():
    speaker = ResponseSpeaker()

    # ✅ 測試直接語音合成
    test_text = "你好，我是你的語音助理，很高興為你服務！"
    audio_file = speaker.text_to_speech(test_text)
    if audio_file:
        #print(f"語音文件已生成: {audio_file}")
        speaker.play_audio(audio_file)


if __name__ == "__main__":
    main()
