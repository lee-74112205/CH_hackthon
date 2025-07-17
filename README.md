# 🎙️ 中文語音助手｜Chinese Voice Assistant

> 🏆 2025 雲湧智生：臺灣生成式 AI 應用黑客松競賽  
> 👤 我的角色：前端互動設計、語音播放與錄音處理、語音文字轉換整合

---

## 🧠 專案簡介

本專案為一款基於 AWS 雲端語音服務的中文語音助手，具備熱詞喚醒、語音辨識、智能命令分類與語音回覆等功能，致力於打造自然流暢的語音交互體驗。

👉 原始碼連結：[Edward43w/CH_hackthon](https://github.com/Edward43w/CH_hackthon)

---

## 💡 我的貢獻（前端）

- 🎛️ 設計並實作語音互動流程（使用者說「你好」喚醒 → 對話 → Polly 回覆）
- 🎙️ 使用 Web Audio API 錄音、MediaRecorder 上傳音訊至後端進行辨識
- 🔊 使用 SpeechSynthesis API 將文字回應轉為語音播放，支援語速調整（停、快一點、慢一點）
- 🔁 控制連續語音互動流程與 UI 更新，強化使用者體驗
- 🔗 前後端整合：使用 Axios 呼叫 Flask API，串接 Whisper 與 Bedrock 服務

---

## ✨ 專案功能總覽

- 🎯 熱詞喚醒：「你好」即啟動語音模式
- 🗣️ 高精度語音辨識：AWS Whisper 模型
- 🤖 智能命令分類：聊天 / 查詢 / 行動指令自動分類（AWS Bedrock）
- 🔊 語音合成回覆：AWS Polly 中文語音
- 🎮 語音控制命令：支援「停」、「快一點」、「慢一點」、「恢復正常」等語速調整
- 🔁 連續互動流程設計：說「再見」結束對話模式並返回待命狀態

---

## 🛠️ 技術架構

### 前端（由我負責）：
- React + Vite 開發框架
- Web Audio API（錄音）
- SpeechSynthesis API（語音播放）
- Axios（與 Flask 後端通信）

### 後端（團隊其他成員）：
- Flask Web Server
- AWS Whisper（語音轉文字）
- AWS Polly（文字轉語音）
- AWS Bedrock（命令分類與自然語言回覆）

---

## 🧪 系統流程簡圖

1. 🟢 **喚醒階段**：監聽「你好」 → 進入指令接收
2. 🎤 **語音辨識**：錄音上傳 → Whisper 轉文字
3. 📚 **分類回應**：文字送至 Bedrock → 判斷用途並產生回覆
4. 🔊 **語音回覆**：Polly 合成語音並由前端播放
5. 🔁 **互動控制**：「再見」結束回合、返回待命狀態

---

## 📸 活動畫面

<img width="2048" height="1365" alt="image" src="https://github.com/user-attachments/assets/03061161-2a41-467e-aac1-1678c8f6a910" />
<img width="2048" height="1152" alt="image" src="https://github.com/user-attachments/assets/1f6b8b24-250e-400e-bc65-9311cc9d0be5" />
<img width="2048" height="1152" alt="image" src="https://github.com/user-attachments/assets/a4e67dd2-7021-4fd5-aaad-b329887b5895" />

---

## 📜 授權

本專案採用 MIT License  
© 2025 中文語音助手開發團隊
