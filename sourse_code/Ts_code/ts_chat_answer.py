import requests
import re
import json

class Chat:
    def __init__(self, token="6ed8ce05fae8cdacdf486d573034eed8b887721a"):
        self.base_url = "https://aistudio.baidu.com/llm/lmapi/v3/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        print(f"模型 chat 已经完成初始化")

    def predict(self, problem):
        payload = {
            "model": "ernie-4.5-turbo-vl",
            "messages": [
                {"role": "system", "content": ""},
                {"role": "user", "content": problem}
            ],
            "temperature": 0.8,
            "top_p": 0.8,
            "stream": False,
            "max_tokens": 2000
        }
        try:
            resp = requests.post(self.base_url, headers=self.headers, json=payload, timeout=10)
            resp.raise_for_status()

            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                res = choices[0]["message"]["content"]
                match = re.search(r'\$(.*?)\$', res)
                if match:
                    final_res = match.group(1)
                    return final_res
                else:
                    return "ER"
            else:
                return "ER"
        except Exception as e:
            print(e)
            return "ER"


if __name__ == "__main__":
    tester = Chat()
    text = "年龄20：性别男，身高180cm 体重 80斤"
    print(tester.predict(f"bmi:帮我从我给你的信息中提取身高与体重，并转为转为m与kg的单位给我(注意单位转换，如'斤->kg')，并用$环绕，格式严格如下例:$1.7m;40kg$，信息为{text}"))
