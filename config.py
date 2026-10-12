import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEP_API_KEY=os.getenv("DEEPSEEP_API_KEY")
DEEPSEEK_BASE_URL=os.getenv("DEEPSEEK_BASE_URL","https://api.deepseek.com")
LLM_MODEL=os.getenv("LLM_MODEL","deepseek-chat")

if not DEEPSEEP_API_KEY:
    raise SystemError("缺少 DEEPSEEP_API_KEY，请检查 .env 文件")


