"""day6： 让模型学会调用工具"""

from datetime import datetime


SEP="="*56

#=======================1.真正的函数=======================
def calculate(expression:str):
    """计算数学表达式。白名单字符检查，防止eval被注入"""
    allowed=set("0123456789+-*/().")
    if not set(expression)<=allowed:
        return "表达式包含不支持的字符，只能包含数字和“+-*/()."
    try:
        return  str(eval(expression))   # eval是Python的内置函数，用于计算表达式
    except Exception as e:
        return f"计算出错：{e}"   # 返回错误信息

def get_current_time()->str:
    """获取当前时间"""
    now=datetime.now()
    weekdays=["一","二","三","四","五","六","日"]
    return f"{now:'%Y-%m-%d %H:%M:%S'}，星期{weekdays[now.weekday()]}"   # 返回当前时间

#-----------------2.工具描述（给模型看的”说明书“）---------------
TOOLS = [
    {
        "type":"function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式。白名单字符检查，防止eval被注入",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type":"function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前时间"
        }
    }
]

#函数名->实际函数的映射表
TOOL_MAP={"calculate":calculate,"get_current_time":get_current_time}

# #--------------------3.完整调用循环-----------------------
# def ask(question:str):
#     messages=[{"role":"user","content":question}]
#     print(f"\n{SEP}\n你:{question}")
#
#     while True:
#         resp=client.chat.completions.create(
#             model=config.LLM_MODEL,
#             messages=messages,
#             tools=TOOLS,
#             temperature=0,
#         )
#         msg=resp.choices[0].message
#
#         #模型没有调用工具 -> 说明它给出了最终回答
#         if not msg.tool_calls:
#             print(f"AI:{msg.content}")
#             break
#         #模型调用工具：把它的”调用请求“存进历史
#         messages.append(msg)
#         for tc in msg.tool_calls:
#             name=tc.function.name
#             args=json.loads(tc.function.arguments)
#             print(f"AI:调用工具'{name}'，参数：{args}")
#             result=TOOL_MAP[name](**args)
#             print(f"[调用结束]{result}")
#
#             messages.append({
#                 "role":"tool",
#                 "tool_call_id":tc.id,
#                 "content":str(result),
#             })
#
