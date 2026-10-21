#临时脚本 test_retyry.py
import config
from openai import OpenAI

#故意传一个错误的base_url，制造连接错误
client = OpenAI(
    api_key=config.DEEPSEEP_API_KEY,
    base_url="https://api.deepseek.com.invalid"
)
import time
for attempt in range(3):
    try:
        client.chat.completions.create(
            model="deepseek-flash",
            messages=[{"role":"user","content":"hello"}]
        )
        break
    except Exception as e:
        print(f"[重试{attempt+1}/3] {type(e).__name__}")
        time.sleep(1*(2**attempt))  # 延迟1秒，指数退避
