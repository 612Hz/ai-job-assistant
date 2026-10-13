"""Day5对照试验：主动制造失败，观察模型行为"""

import config
from openai import OpenAI

from llm import client

SEP="="*56

#=================实验一：temperature 对实验的影响===================
def exp_temperature():
    question="用一句话推荐一部电影"
    for temp in [0,0.7,1.5]:
        print(f"\n{SEP}\ntemperature = {temp}\n{SEP}")
        for i in range(3):
            resp=client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role":"user","content":question}],
                temperature=temp,
            )
            print(f"{i+1} {resp.choices[0].message.content}")

#=================实验二：token 与成本============================
def exp_token():
    samples=[
        ("超短","你好"),
        ("短","请用一句话介绍python"),
        ("中","请用200字介绍python的历史、特点、应用场景和优缺点"),
        ("长","请用500字介绍python的历史、设计哲学、语法特点、常用库、应用场景、优缺点和学习建议")
    ]
    print(f"{'类型':6}|{'输入token':>8}|{'输出token':>8}|{'合计':>6}")
    print("-"*46)
    for label,text in samples:
        resp=client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[{"role":"user","content":text}],
        )
        u=resp.usage
        print(f"{label:6}|{u.prompt_tokens:>8}|{u.completion_tokens:>8}|{u.total_tokens:>6}")




#=================实验三：多轮对话的上下文膨胀=======================
def exp_context():
    history=[{"role":"system","content":"你是一个乐于助人的助手。"}]
    question=[
        "你好", "今天想聊聊技术","我想学AI应用开发","应该从哪里开始",
        "需要学RAG吗","Agent呢","工程化重要吗","怎么证明我做过",
        "项目要上线吗","那我现在该做什么",
    ]
    print(f"{'轮次':4}|{'本次输入token':>12}|{'消息条数':>8}")
    print("-"*40)
    for i,q in enumerate(question,1):
        history = [{"role": "system", "content":q}]
        resp = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=history
        )
        history.append({"role": "assistant", "content": resp.choices[0].message.content})
        print(f"{i:4}|{resp.usage.prompt_tokens:>12}|{len(history):>8}")


if __name__=='__main__':
    which=input("跑哪个实验？输入1/2/3：").strip()
    print(f"[调试] 你输入的字符是：{which!r}")
    if which=='1':
        exp_temperature()
    elif which=='2':
        exp_token()
    elif which=='3':
        exp_context()
    else:
        print("未识别到输入")