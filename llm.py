from openai import OpenAI
from openai.resources.skills import content

import config
import json

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
            stream=True,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"[调用失败] {type(e).__name__}: {e}")
        return None

def chat_stream(messages):
    """流式输出：逐段yield文本片段"""
    try:
        stream=client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            stream=True,
        )
        for chunk in stream:
            delta=chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        print(f"\n[调用失败] {type(e).__name__}:{e}")
        return

def chat_with_tools(messages,tools,tool_map,max_rounds=8,on_tool_call=None):
    """
    带工具调用的对话循环（会原地修改messages）。
    :param messages:
    :param tools:
    :param tool_map: {函数名：函数对象}
    :param max_rounds: 最大轮次上限（防止死循环）
    :param on_tool_call: 回调（name，args）,用于打印日志
    :return: 出错是返回None
    """
    try:
        for _ in range(max_rounds):
            resp=client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                tools=tools,
            )
            msg=resp.choices[0].message

            #没有工具调用——>这就是最终回答
            if not msg.tool_calls:
                return msg.content

            messages.append(msg)
            for tc in msg.tool_calls:
                name=tc.function.name
                args=json.loads(tc.function.arguments or "{}")
                if on_tool_call:
                    on_tool_call(name,args)

                fn=tool_map.get(name)
                result=fn(**args) if fn else f"未知工具：{name}"

                messages.append({
                    "role":"tool",
                    "tool_call_id":tc.id,
                    "content":str(result),
                })
        return "(工具调用次数过多，已停止）"
    except Exception as e:
        print(f"[调用失败] {type(e).__name__}: {e}")
        return None
