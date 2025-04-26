# ===== 更新版 recorder.py =====

import sounddevice as sd
import numpy as np
import time
import os
from scipy.io.wavfile import write
from datetime import datetime

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, silence_threshold=70000, silence_duration=1.5):
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration
        self.audio_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'audio_input'))
        os.makedirs(self.audio_dir, exist_ok=True)


    def listen_forever(self, on_heard_callback):
        print("🎧 進入持續監聽模式...")

        frame_duration = 0.3
        frame_size = int(self.sample_rate * frame_duration)
        stream = sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype='int16')
        stream.start()

        recording = []
        last_voice_time = time.time()
        speaking = False

        try:
            while True:
                frame, overflowed = stream.read(frame_size)
                if overflowed:
                    print("⚠️ 音訊 overflow!")

                volume = np.linalg.norm(frame)
                #debug用音量
                # print(volume)

                if volume > self.silence_threshold:
                    if not speaking:
                        speaking = True
                    recording.append(frame)
                    last_voice_time = time.time()
                else:
                    if speaking and (time.time() - last_voice_time) > self.silence_duration:
                        audio_data = np.concatenate(recording, axis=0)
                        filename = os.path.join(self.audio_dir, f"recording.wav")
                        write(filename, self.sample_rate, audio_data)

                        if on_heard_callback:
                            on_heard_callback(filename)

                        recording = []
                        speaking = False

        except KeyboardInterrupt:
            print("👋 停止持續監聽")
        finally:
            stream.stop()
            stream.close()
