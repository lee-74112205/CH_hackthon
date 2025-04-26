import os
import wave
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from datetime import datetime
import time

# 修正：載入正確的 .env 路徑（從 backend/config/.env）
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config', '.env'))
load_dotenv(env_path)

class AudioRecorder:
    def __init__(self):
        self.sample_rate = int(os.getenv('SAMPLE_RATE', 16000))
        self.channels = int(os.getenv('CHANNELS', 1))
        self.chunk_duration = 0.5  # 每0.5秒錄一個區塊
        self.silence_threshold = 0.001
        self.silence_duration = 3

        # 修正：確保 audio_dir 是絕對路徑
        self.audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'audio'))
        os.makedirs(self.audio_dir, exist_ok=True)

    def record(self):
        """連續錄音直到偵測3秒無聲，自動停止，並儲存成 WAV 檔"""
        print("🎙️ 開始錄音，請開始說話...")

        recording = []
        last_voice_time = None
        block_size = int(self.sample_rate * self.chunk_duration)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(self.audio_dir, f"recording_{timestamp}.wav")

        while True:
            block = sd.rec(block_size, samplerate=self.sample_rate, channels=self.channels, dtype='float32')
            sd.wait()
            energy = np.linalg.norm(block) / block_size
            recording.append(block)

            if energy > self.silence_threshold:
                last_voice_time = time.time()

            if last_voice_time is not None and (time.time() - last_voice_time > self.silence_duration):
                print("⏹️ 偵測到3秒無聲，自動停止錄音")
                break

        recording = np.concatenate(recording, axis=0)

        with wave.open(output_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes((recording * 32767).astype(np.int16).tobytes())

        print(f"✅ 錄音完成，已儲存為 {output_filename}")
        return output_filename

    def is_silent(self, audio_data, silence_threshold=500):
        """檢查是否是靜音（沒變動）"""
        return np.mean(np.abs(audio_data)) < silence_threshold

    def wait_for_speech(self):
        """保留原本 wait_for_speech，不變"""
        print("等待語音輸入...")
        while True:
            audio_data = sd.rec(
                int(self.sample_rate * 0.1),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.int16
            )
            sd.wait()

            if not self.is_silent(audio_data):
                print("檢測到語音!")
                return True
