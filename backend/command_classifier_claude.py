import os
import json
import boto3
from dotenv import load_dotenv
from datetime import datetime
import requests

# ✅ 正確加載環境變數
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config', '.env'))
load_dotenv(env_path)

class CommandClassifier:
    def __init__(self):
        # 設置 AWS Bedrock 客戶端
        self.client = boto3.client(
            service_name="bedrock-runtime",
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-west-2')
        )

        # 設置模型 ID
        self.model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        # ✅ 正確載入 assets/command_type.json
        json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'command_type.json'))
        with open(json_path, 'r', encoding='utf-8') as f:
            self.reference_data = json.load(f)

        self.available_functions = [{
            "function_name": "web_search",
            "description": "搜索網絡獲取實時信息",
            "parameters": [{
                "name": "query",
                "type": "string",
                "description": "搜索關鍵詞"
            }]
        }]

    def _send_to_model(self, prompt):
        """發送提示詞到 Claude 模型並獲取回應"""
        body = json.dumps({
            "max_tokens": 512,
            "messages": [{"role": "user", "content": prompt}],
            "anthropic_version": "bedrock-2023-05-31"
        })

        try:
            response = self.client.invoke_model(
                body=body,
                modelId=self.model_id,
                contentType="application/json"
            )
            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]
        except Exception as e:
            print(f"模型調用錯誤: {str(e)}")
            return "無法獲取模型回應"

    def classify_command(self, text):
        """分類輸入命令"""
        examples = "\n".join([f"- 輸入：{item['command']}  類型：{item['command_type']}" for item in self.reference_data])

        prompt = f"""
        根据以下示例對命令進行分類。
        示例：
        {examples}
        請對以下輸入進行分類：
        輸入："{text}"
        請只回復以下三種類型之一：
        - 聊天
        - 查詢
        - 行動
        """

        # print("\n=== 提示詞內容 ===")
        # print(prompt)
        # print("=== 提示詞結束 ===\n")

        result = self._send_to_model(prompt).strip()
        #print(f"模型響應: {result}\n")

        if '查' in result or '詢' in result:
            print("分類結果: 查詢")
            return '查詢'
        elif '行' in result or '動' in result:
            print("分類結果: 行動")
            return '行動'
        else:
            print("分類結果: 聊天")
            return '聊天'

    def chat_with_gemini(self, text):
        """與 Claude 聊天"""
        prompt = f"""
        你是一個友善的AI助手，請用自然、友好的方式回應用戶的對話。
        請用繁體中文回覆。
        用戶說：{text}
        """
        # print("\n=== 聊天提示詞內容 ===")
        # print(prompt)
        # print("=== 提示詞結束 ===\n")

        result = self._send_to_model(prompt).strip()
        print(f"Claude回應: {result}\n")
        return result

    def save_chat_history(self, command, response, command_type):
        """保存聊天歷史"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chat_data = {"timestamp": timestamp, "command": command, "response": response, "command_type": command_type}

        # ✅ 保存到 data/chat_history
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'chat_history'))
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, f"chat_{timestamp}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)

        #print(f"聊天記錄已保存至: {file_path}\n")

    def web_search(self, query):
        """網路搜尋"""
        search_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        cx = os.getenv('GOOGLE_SEARCH_CX')
        url = "https://www.googleapis.com/customsearch/v1"
        params = {'key': search_api_key, 'cx': cx, 'q': query}

        try:
            response = requests.get(url, params=params)
            results = response.json()

            if 'items' in results:
                return [{
                    'title': item['title'],
                    'snippet': item['snippet'],
                    'link': item['link']
                } for item in results['items'][:3]]
            return []
        except Exception as e:
            print(f"搜索出錯: {str(e)}")
            return []

    def handle_query(self, text):
        """處理查詢命令"""
        prompt = f"""
        你是一個專業的搜索助手。用戶想要查詢一些信息，請幫我生成合適的搜索關鍵詞。
        用戶查詢：{text}
        """

        # print("\n=== 查詢提示詞內容 ===")
        # print(prompt)
        # print("=== 提示詞結束 ===\n")

        search_query = text
        # print(f"生成的搜索關鍵詞: {search_query}")

        search_results = self.web_search(search_query)

        results_prompt = f"""
        你是一個資訊助理，請根據以下 Google 搜尋結果，直接用繁體中文回答使用者的問題：
        問題：{text}

        請務必：
        1. 回答要簡潔，重點清楚。
        2. 若無明確答案，也要說「查無確切結果」。
        3. 不要回覆與問題無關的資訊。

        搜尋結果：
        {json.dumps(search_results, ensure_ascii=False, indent=2)}
        """

        final_response = self._send_to_model(results_prompt)
        return final_response.strip()

    def save_query_history(self, command, response, command_type):
        """保存查詢歷史"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        query_data = {"timestamp": timestamp, "command": command, "response": response, "command_type": command_type}

        # ✅ 保存到 data/query_history
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'query_history'))
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, f"query_{timestamp}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(query_data, f, ensure_ascii=False, indent=2)

        #(f"查詢記錄已保存至: {file_path}\n")

    def handle_movement(self, text):
        """處理行動命令"""
        # ✅ 載入 assets/movement_deployment.json
        movement_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'movement_deployment.json'))
        with open(movement_json_path, 'r', encoding='utf-8') as f:
            movement_data = json.load(f)

        prompt = f"""
        你是一個專業的機器人動作規劃助手。請根據以下系統設定和用戶的任務，生成詳細的動作順序和說明。

        系統可用的動作清單：
        {json.dumps(movement_data['動作清單'], ensure_ascii=False, indent=2)}

        參考任務範例：
        {json.dumps(movement_data['任務拆解'], ensure_ascii=False, indent=2)}

        當前用戶任務：{text}

        請按照以下格式返回：
        {{
            "動作順序": ["動作代號1", "動作代號2", ...],
            "說明": [
                "詳細步驟1",
                "詳細步驟2",
                ...
            ]
        }}

        請確保：
        1. 動作順序使用動作清單中的代號
        2. 說明要詳細且符合實際執行順序
        3. 回覆必須是有效的JSON格式，並使用```json 包裹
        """

        # print("\n=== 行動規劃提示詞內容 ===")
        # print(prompt)
        # print("=== 提示詞結束 ===\n")

        result = self._send_to_model(prompt).strip()
        #print(f"Claude回應: {result}\n")

        try:
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0].strip()
            else:
                json_str = result.strip()

            movement_plan = json.loads(json_str)

            if not isinstance(movement_plan, dict) or '動作順序' not in movement_plan or '說明' not in movement_plan:
                raise ValueError("JSON格式不符合要求")

            return movement_plan

        except (json.JSONDecodeError, ValueError) as e:
            print(f"警告：無法解析回應為JSON格式 - {str(e)}")
            return {"動作順序": [], "說明": ["無法生成有效的動作計劃"]}

    def save_movement_history(self, command, response, command_type):
        """保存行動歷史"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        movement_data = {"timestamp": timestamp, "command": command, "movement_plan": response, "command_type": command_type}

        # ✅ 保存到 data/movement_history
        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', 'movement_history'))
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, f"movement_{timestamp}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(movement_data, f, ensure_ascii=False, indent=2)

        #print(f"行動計劃已保存至: {file_path}\n")

if __name__ == "__main__":
    classifier = CommandClassifier()

    test_commands = [
        "幫我查行天宮附近的披薩店"
    ]

    #print("開始測試命令分類：\n")

    for command in test_commands:
        print(f"測試命令: {command}")
        command_type = classifier.classify_command(command)
        print(f"分類結果: {command_type}")

        if command_type == '聊天':
            chat_response = classifier.chat_with_gemini(command)
            classifier.save_chat_history(command, chat_response, command_type)
        elif command_type == '查詢':
            query_response = classifier.handle_query(command)
            classifier.save_query_history(command, query_response, command_type)
            print(f"查詢結果: {query_response}")
        elif command_type == "行動":
            movement_plan = classifier.handle_movement(command)
            classifier.save_movement_history(command, movement_plan, command_type)
            print(f"行動計劃：")
            print(json.dumps(movement_plan, ensure_ascii=False, indent=2))

        print("-" * 50)
