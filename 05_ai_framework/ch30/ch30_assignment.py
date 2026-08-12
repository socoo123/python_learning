"""
Ch30 作业:LangChain 基础(LCEL)。

主线场景(极客商城客服问答机器人):Ch28/29 每次「拼 prompt → 调模型 → 解析」都手写三步,
本章用 LangChain 的 LCEL 把这条链声明式拼起来——`prompt | model | parser`,像 Unix 管道。
再做两件事:① 带记忆的客服问答(维护 messages 列表);② 批量处理评论(chain.batch)。

设计要点:本作业【不调真实 LLM】。model 步骤用 RunnableLambda 包一个普通函数充当
FakeModel;上线时把它换成 ChatAnthropic/ChatOpenAI,链的其余部分一行不动(tutorial §30.9)。

8 个函数。在每处 TODO 写实现,然后:

    uv sync --extra ai
    uv run pytest 05_ai_framework/ch30/test_ch30_assignment.py -v

全绿 = 你掌握了 Ch30。

每题 docstring 的【对应小节】指向 tutorial.md。卡住 → 回查对应 §。

依赖:langchain-core(PromptTemplate / RunnableLambda / StrOutputParser 都在它里面)。
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

# 客服问答模板:{history} 是渲染好的对话历史(format_history 产出),{question} 是当前问题。
QA_TEMPLATE = "你是极客商城的客服,基于对话历史简洁回答。\n{history}用户问:{question}\n客服答:"


# ========== §30.2 模板:build_prompt ==========


def build_prompt(template: str) -> PromptTemplate:
    """
    【模板 · §30.2】把模板字符串包成 LangChain 的 PromptTemplate 对象。

    示例:
        p = build_prompt("回答:{q}")
        p.invoke({"q": "你好"}).to_string()  -> "回答:你好"
        build_prompt("{greeting},{name}").format(greeting="Hi", name="Bob")  -> "Hi,Bob"

    提示:
        return PromptTemplate.from_template(template)
        注意 invoke 返回的是 PromptValue 对象不是 str,要纯文本用 .to_string()/.format()。
    """
    # TODO: PromptTemplate.from_template(template)
    ...


# ========== §30.3 包装成 Runnable:as_runnable ==========


def as_runnable(fn) -> RunnableLambda:
    """
    【Runnable · §30.3】把任意普通函数 fn 包成 RunnableLambda,让它能用 | 串进链子。
    本作业用它包 FakeModel(假装是 LLM 的普通函数);真实场景这一步换成 ChatAnthropic。

    示例:
        r = as_runnable(lambda s: s.upper())
        r.invoke("abc")  -> "ABC"
        chain = r | as_runnable(lambda s: s + "!")
        chain.invoke("hi")  -> "HI!"

    提示:
        return RunnableLambda(fn)
    """
    # TODO: RunnableLambda(fn)
    ...


# ========== §30.4 LCEL 组装:build_chain ==========


def build_chain(prompt: PromptTemplate, model_runnable, parser):
    """
    【LCEL · §30.4】用管道 | 把 prompt → model → parser 串成一条链(返回 Runnable)。

    ⚠️ 关键细节:prompt 步输出的是 PromptValue 对象(不是 str)。真实 ChatModel 能直接吃
    PromptValue;但本作业的 FakeModel 是只会 f"{s}" 拼接的普通函数,遇到 PromptValue 会
    渲染成对象 repr(乱码)。所以中间插一个 to_text 步,把 PromptValue 转成纯字符串。

    示例:
        chain = build_chain(build_prompt("Q:{q}"), as_runnable(lambda s: f"A:{s}"), StrOutputParser())
        chain.invoke({"q": "你好"})  -> "A:Q:你好"

    提示:
        to_text = RunnableLambda(lambda v: v.to_string() if hasattr(v, "to_string") else str(v))
        return prompt | to_text | model_runnable | parser
    """
    # TODO: 定义 to_text(duck typing:有 to_string 就用,否则 str(v));再 prompt | to_text | model | parser
    ...


# ========== §30.5 单条执行:run_chain ==========


def run_chain(chain, variables: dict) -> str:
    """
    【执行 · §30.5】把 variables 喂进链子,拿最终输出。一个 invoke = 渲染+调用+解析。

    示例:
        chain = build_chain(build_prompt("Q:{q}"), as_runnable(lambda s: f"A:{s}"), StrOutputParser())
        run_chain(chain, {"q": "你好"})  -> "A:Q:你好"

    提示:
        return chain.invoke(variables)
    """
    # TODO: chain.invoke(variables)
    ...


# ========== §30.6 批量执行:batch_run ==========


def batch_run(chain, inputs: list[dict]) -> list[str]:
    """
    【批量 · §30.6】用 chain.batch 一次跑多条输入(内部并发,比 for 循环逐条 invoke 快)。
    输入 list[dict](每个元素是一条链的 variables),输出 list[str],顺序与输入一一对应。

    示例(批量分析评论的场景):
        chain = build_chain(build_prompt("问:{q}"), as_runnable(lambda s: f"答:{s}"), StrOutputParser())
        batch_run(chain, [{"q": "a"}, {"q": "b"}, {"q": "c"}])
            -> ["答:问:a", "答:问:b", "答:问:c"]
        batch_run(chain, [])  -> []

    提示:
        return chain.batch(inputs)   # 别写 for 循环
    """
    # TODO: chain.batch(inputs)
    ...


# ========== §30.7 对话记忆:append_turn / format_history ==========


def append_turn(history: list[dict], user: str, assistant: str) -> list[dict]:
    """
    【记忆 · §30.7】往对话历史追加一轮 user/assistant,【不修改原 history】。
    LLM 无状态,记忆 = 客户端维护 messages 列表,每轮追加、下次请求带上全部历史。

    示例:
        append_turn([], "你好", "你好呀")
            -> [{"role": "user", "content": "你好"}, {"role": "assistant", "content": "你好呀"}]

    提示(别 mutate 入参——可变默认参数陷阱 Ch02):
        return [*history, {"role": "user", "content": user}, {"role": "assistant", "content": assistant}]
    """
    # TODO: 返回 history 副本 + 追加 user 和 assistant 两条
    ...


def format_history(history: list[dict]) -> str:
    """
    【记忆 · §30.7】把 messages 列表渲染成文本,塞进 prompt 的 {history} 占位符。
    规则:user → "用户:{content}",assistant → "客服:{content}",每条一行(以 \\n 结尾)。

    示例:
        format_history([])  -> ""
        format_history([{"role": "user", "content": "有货吗"},
                        {"role": "assistant", "content": "有的"}])
            -> "用户:有货吗\\n客服:有的\\n"

    提示:
        ROLE_LABEL = {"user": "用户", "assistant": "客服"}
        逐条 f"{ROLE_LABEL[m['role']]}:{m['content']}\\n" 收集后 "" join。
    """
    # TODO: 遍历 history,user→"用户:..." assistant→"客服:...",每条带 \n,join 返回
    ...


# ========== §30.8 综合:chat_once ==========


def chat_once(model_runnable, question: str, history: list[dict]) -> tuple[str, list[dict]]:
    """
    【综合 · §30.8】带记忆的客服问答——复用前面全部函数,完成一轮问答闭环。
    返回 (回答文本, 更新后的新历史);【不修改入参 history】(不可变数据风格)。

    一轮做四件事:
      ① build_prompt(QA_TEMPLATE) 建模板
      ② build_chain(prompt, model_runnable, StrOutputParser()) 组链
      ③ run_chain(chain, {"history": format_history(history), "question": question}) 拿回答
      ④ append_turn(history, question, answer) 把这轮追加进历史
      返回 (answer, 新历史)

    示例(model 是「复读问题」的 FakeModel):
        fake = as_runnable(lambda s: "亲," + s.rsplit("用户问:", 1)[-1].splitlines()[0])
        answer, h = chat_once(fake, "有货吗", [])
        answer  -> "亲,有货吗"
        h       -> [{"role":"user","content":"有货吗"}, {"role":"assistant","content":"亲,有货吗"}]

    提示:考的就是【复用】——别自己重写 build_prompt/build_chain/run_chain/append_turn 的逻辑。
    """
    # TODO: build_prompt → build_chain → run_chain(带 format_history)→ append_turn;返回 (answer, 新历史)
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 演示:FakeModel 复读问题;真实用法把 as_runnable(...) 换成 ChatAnthropic(...) 即可
    fake = as_runnable(lambda s: "亲," + s.rsplit("用户问:", 1)[-1].splitlines()[0])
    history: list[dict] = []
    for q in ["有货吗", "发什么快递"]:
        answer, history = chat_once(fake, q, history)
        print(f"你: {q}\n客服: {answer}")
    print("批量:", batch_run(build_chain(build_prompt("问:{q}"), fake, StrOutputParser()),
                             [{"q": "a"}, {"q": "b"}]))
