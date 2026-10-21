import tools

@tools.tool
def reverse_text(text:str)->str:
    """把文本反转。当用户要求倒序输出文字时使用

    Args:
        text:要反转的文本
        """
    return text[::-1]

print("已注册的工具:",list(tools.get_tool_map().keys()))
print("自动生成的schema：",tools.get_tools()[-1])