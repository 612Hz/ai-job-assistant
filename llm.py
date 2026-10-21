from openai import OpenAI
import time

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

def chat_with_tools_stream(messages,tools,tool_map,max_rounds=8,on_tool_call=None):
    """带工具的对话，最终回答流式输出。
    工具调用接对岸是非流式的（因为工具调用是同步的，且返回的是json指令，所以这里没有stream参数）
    一旦模型开始生成最终回答，就切到流式
    """
    try:
        #阶段A：循环处理工具调用（非流式）
        for _ in range(max_rounds):
            resp=client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                tools=tools,
                temperature=0
            )
            msg=resp.choices[0].message

            #模型这次不掉工具了->这是最终回答,要切回到流式
            if not msg.tool_calls:
                stream=client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    tools=tools,
                    temperature=0,
                    stream=True,
                )
                for chunk in stream:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                return

            #模型要调工具，执行并回传（非流式）
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
        yield "(工具调用次数过多，已停止）"
    except Exception as e:
        print(f"[调用失败] {type(e).__name__}: {e}")
        return


#带重试的调用，作用：防止因为网络问题导致的偶尔性错误
def chat_with_retry(messages,retyries=3,base_delay=1.0):
    """带指数退避重试的调用，失败后延迟1s、2s、4s再试"""
    for attempt in range(retyries):
        try:
            resp=client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
            )
            return resp.choices[0].message.content
        except Exception as e:
            if attempt==retyries-1:
                raise   # 记录日志后仍把异常交给上层
            delay=base_delay*(2**attempt)
            print(f"[重试{attempt+1}/{retyries}] {type(e).__name__},{delay}后重试")
            time.sleep(delay)
    return  None