from openai import OpenAI
import config

client=OpenAI(
    api_key=config.DEEPSEEP_API_KEY,
    base_url=config.DEEPSEEK_BASE_URL,
)

def chat(messages):
    """统一的对话吐口，后面的模块都调用它"""
    try:
        resp=client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            stream=False,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[调用失败] {type(e).__name__}: {e}")
        return None
