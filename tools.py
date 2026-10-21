#工具定义与注册机制。加一个工具 = 写一个带@tool的函数
import inspect  # 用于获取函数的签名和类型提示
import types
from datetime import datetime  # 用于获取当前时间
from typing import get_type_hints,get_origin,get_args,Union # 用于获取函数的类型提示

#内部登记表 作用：存储工具的schema和函数对象
_TOOL_SCHEMAS:dict ={}
_TOOL_FUNCS :dict ={}



# python类型-->JSON Schema 类型  作用：将Python类型转换为JSON Schema类型
_TYPE_MAP ={
    str:"string",
    int:"integer",
    float:"number",
    bool:"boolean"
}

def _json_type(tp)->dict:
    """把python类型注解递归转换成JSON Schema的类型描述"""
    origin = get_origin(tp)    # 获取类型注解的原始类型

    #get_args()的作用
    # get_args(List[str])           # → (str,)
    # get_args(Dict[str, int])      # → (str, int)
    # get_args(Optional[int])       # → (int, NoneType)

    #1)Optional[X] / Union[X,None] / X|None
    if origin is Union or origin is types.UnionType:
        #比如注解是 Optional[str]，get_args() 返回 (str, NoneType)
        #所以这里过滤掉 NoneType，只剩 str，再递归转换。这就把"可为空的 str"还原成了"str"的 schema。
        args =[a for a in get_args(tp) if a is not type(None)]
        if len(args)==1:
            return _json_type(args[0])
        return {"type":"string"}

    #2) list[X] / List[X]
    if origin is list:
        args = get_args(tp)          #args = get_args(tp)  list[str] → (str,)
        item = args[0] if args else str
        return {"type":"array","items":_json_type(item)}

    #3) dict[str,Y] / Dict[str,Y]   只取 value 类型（key 在 JSON 里总是字符串，无需转换
    if origin is dict:
        args = get_args(tp)
        val = args[1] if len(args) >1 else str
        return {"type":"object","additionalProperties":_json_type(val)}

    #4)基础类型  走到这里说明 tp 不是 Union/list/dict，即 str/int/float/bool 这类；
    # 查对照表，查不到（未知类型）就保守地兜底成 "string"。
    return {"type":_TYPE_MAP.get(tp,"string")}


def _is_optional(tp)->bool:
    """判断类型是否Optional（Union 里包含None）"""
    origin = get_origin(tp)
    if origin is Union or origin is types.UnionType:
        # 第 51 行：分支类型列表里若含 NoneType，就是 Optional；
        # 例如 Optional[int]→(int,NoneType)→True；Union[int,str]→False。
        return type(None) in get_args(tp)
    return False


# 从docstring 的‘Args：’段里提取参数说明  作用：生成JSON Schema的参数说明
def _param_desc(doc:str,name:str):
    """从docstring 的‘Args：’段里提取参数说明。"""
    for line in (doc or "").splitlines():
        line=line.strip()
        for sep in [":","：","-","--","——"]:
            prefix = f"{name}{sep}"
            if line.startswith(prefix):
                return line[len(prefix):].strip()
    return name

# 装饰器：把函数注册为LLM工具，自动生成JSON Schema  作用：将函数注册为LLM工具，并生成JSON Schema
def tool(func):
    """装饰器：把函数注册为LLM工具，自动生成JSON Schema。"""
    sig=inspect.signature(func)   # 反射：拿到函数的参数列表（参数名，默认值，类型）
    hints=get_type_hints(func)   # 把类型注解解析成真正的类型对象，处理字符串注解等情况

    props,required ={},[]
    for name,p in sig.parameters.items():   # 遍历函数的参数
        tp= hints.get(name,str)       #按定义顺序遍历；name=参数名字符串，p=Parameter 对象。
        prop = _json_type(tp)    # 第 75 行：把 Python 类型递归转成 JSON Schema 片段，
                                 # 如 list[int] → {"type":"array","items":{"type":"integer"}}。

        prop["description"]=_param_desc(func.__doc__ or "",name)

        #有默认信息就把默认值写进schema（告诉模型可以不填）
        if p.default is not inspect.Parameter.empty:
            prop["default"]=p.default

        props[name]=prop

        # 第 79 行：inspect.Parameter.empty 是"没有默认值"的哨兵对象，
        #必填判断：没有默认值且不是Optional
        has_default = p.default is not inspect.Parameter.empty
        if not has_default and not _is_optional(tp):
            required.append(name)
    _TOOL_SCHEMAS[func.__name__]={   # 将工具的schema存储在登记表中
        "type":"function",
        "function":{
            "name":func.__name__,   # 工具的名称
            "description":(func.__doc__ or "").strip().splitlines()[0] if func.__doc__ else "",   # 工具的说明
            "parameters":{
                "type":"object",
                "properties":props,
                "required":required
            }
        }
    }
    _TOOL_FUNCS[func.__name__]=func
    return func

# 返回所有工具的schema列表，拱LLM使用
def get_tools() ->list:
    """返回所有工具的schema列表，拱LLM使用。"""
    return list(_TOOL_SCHEMAS.values())  #作用：返回所有工具的schema列表，供LLM使用

# 返回{函数名：函数对象}，拱执行时快速查找
def get_tool_map()->list:
    """返回{函数名：函数对象}，拱执行时快速查找"""
    return dict(_TOOL_FUNCS)   # 返回一个副本字典，包含所有工具的函数名和函数对象，供执行时快速查找

#=======================1.真正的函数=======================
@tool
def calculate(expression:str):
    """计算数学表达式。白名单字符检查，防止eval被注入"""
    allowed=set("0123456789+-*/().")
    if not set(expression)<=allowed:
        return "表达式包含不支持的字符，只能包含数字和“+-*/()."
    try:
        return  str(eval(expression))   # eval是Python的内置函数，用于计算表达式
    except Exception as e:
        return f"计算出错：{e}"   # 返回错误信息

@tool
def get_current_time()->str:
    """获取当前时间"""
    now=datetime.now()
    weekdays=["一","二","三","四","五","六","日"]
    return f"{now:%Y-%m-%d %H:%M:%S}，星期{weekdays[now.weekday()]}"   # 返回当前时间





















# #-----------------2.工具描述（给模型看的”说明书“）---------------
# TOOLS = [
#     {
#         "type":"function",
#         "function": {
#             "name": "calculate",
#             "description": "计算数学表达式。白名单字符检查，防止eval被注入",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "expression": {
#                         "type": "string",
#                         "description": "数学表达式"
#                     }
#                 },
#                 "required": ["expression"]
#             }
#         }
#     },
#     {
#         "type":"function",
#         "function": {
#             "name": "get_current_time",
#             "description": "获取当前时间"
#         }
#     }
# ]
#
# #函数名->实际函数的映射表
# TOOL_MAP={"calculate":calculate,"get_current_time":get_current_time}

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
