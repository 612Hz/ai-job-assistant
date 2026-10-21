import json
import config
from openai import OpenAI
from pydantic import BaseModel,ValidationError

client=OpenAI(api_key=config.DEEPSEEP_API_KEY,base_url=config.DEEPSEEK_BASE_URL)

#用pydantic定义“期望的数据结构”
class JDInfo(BaseModel):    # 职位信息
    company:str    # 公司
    title:str    # 职位
    skills: list[str]    # 技能列表

JD_TEXT="字节跳动招聘大模型应用开发工程师，要求掌握python、LangChain、向量数据库、熟悉Docker，月薪20-40k。"

def parse_jd(text:str):
    prompt=(
        f"从下面的JD提取公司、职位、技能列表，"
        f"以JSON格式输出，字段为company/title/skills ；\n{text}"
    )
    resp=client.chat.completions.create(
        model=config.LLM_MODEL,
        messages=[
            {"role":"user","content":prompt}
        ],
        response_format={"type":"json_object"},    #response_format: 强制json格式
        stream=False
    )

    raw=resp.choices[0].message.content
    print("模型原始输出：",raw)

    try:
        data=json.loads(raw)
        jd=JDInfo(**data)   # 将data解析为JDInfo对象
        print("校验通过：",jd)
        return jd
    except (json.JSONDecodeError,ValidationError) as e:
        print(f"解析/校验失败:{e}")
        return None

parse_jd(JD_TEXT)