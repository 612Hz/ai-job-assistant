import llm
import tools

history=[{"role":"system","content":"你是一个乐于助人的ai助手。"}]

def main():
    print("Ai助手已启动，输入/reset 清空上下文，输入 exit 退出")
    while True:
        q=input("\n你：").strip()
        if not q:
            continue
        if q in ("exit","quit"):
            print("再见！")
            break
        if q=="/reset":
            del history[1:]
            print("已清理上下文")
            continue

        history.append({"role":"user","content":q})

        #------------流式输出---------------
        # print("\nAI: ",end="",flush=True)   #
        # full=""
        # for piece in llm.chat_stream(history):
        #     print(piece,end="",flush=True)   # 实时输出
        #     full+=piece     #如果漏了它，history里就少了用户输入的完整内容
        #
        # if not full:      #一个碎片都没拿到，撤回本轮提问
        #     history.pop()
        #     continue

        #----------------工具调用-------------
        ans=llm.chat_with_tools(
            history,
            tools.TOOLS,
            tools.TOOL_MAP,
            on_tool_call=lambda n,a:print(f"[调用工具] {n}({a})"),
        )
        if ans is None:
            history.pop()
            continue
        print("\nAI:",ans)
        history.append({"role":"assistant","content":ans})

if __name__=="__main__":
    main()