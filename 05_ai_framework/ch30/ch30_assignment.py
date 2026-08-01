"""
Ch30 作业:LangChain 基础(LCEL)。

Ch28/29 每次「拼 prompt → 调模型 → 解析」很重复。LangChain 用 LCEL
(LangChain Expression Language)把这条链像 Unix 管道一样声明式拼起来:`prompt | model | parser`。

设计要点:本作业【不调真实 LLM】。"model" 步骤用 RunnableLambda 包一个普通函数
(返回固定/echo 文本)充当 FakeModel。真实用法把 RunnableLambda 换成 ChatAnthropic/ChatOpenAI 即可。

5 个函数。在每处 TODO 写实现,然后:

    uv run pytest 05_ai_framework/ch30/test_ch30_assignment.py -v

全绿 = 你掌握了 Ch30。

依赖:langchain-core(PromptTemplate / RunnableLambda / StrOutputParser 都在它里面)。
"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda


# ========== §30.2 模板:build_prompt ==========


def build_prompt(template: str) -> PromptTemplate:
    """
    【模板 · §30.2】把模板字符串包成 LangChain 的 PromptTemplate 对象。

    示例:
        p = build_prompt("回答:{q}")
        p.invoke({"q": "你好"})   -> "回答:你好"

    思路:
        return PromptTemplate.from_template(template)
    """
    # TODO: PromptTemplate.from_template(template)
    ...


# ========== §30.3 包装成 Runnable:as_runnable ==========


def as_runnable(fn) -> RunnableLambda:
    """
    【Runnable · §30.3】把任意普通函数 fn 包成 RunnableLambda,这样它能用 | 串进链子。
    本作业里用它包一个 FakeModel 函数(真实场景换成 ChatModel)。

    示例:
        r = as_runnable(lambda s: s.upper())
        r.invoke("abc")   -> "ABC"

    思路:
        return RunnableLambda(fn)
    """
    # TODO: RunnableLambda(fn)
    ...


# ========== §30.4 LCEL 组装:build_chain ==========


def build_chain(prompt: PromptTemplate, model_runnable, parser):
    """
    【LCEL · §30.4】用管道 | 把 prompt → model → parser 串成一条链(返回 Runnable)。
    这是 LCEL 的核心:声明式组合,像 Unix 管道 a | b | c。

    ⚠️ 细节:prompt.invoke 返回的是 PromptValue 对象(不是 str)。真实 ChatModel 能直接
    吃 PromptValue;但本作业的 FakeModel(RunnableLambda 包的普通函数)只会 f"{s}" 拼接,
    遇到 PromptValue 会渲染成乱码。所以中间加一个 to_text 步,把 PromptValue 转成纯字符串。

    示例:
        chain = build_chain(prompt, model_runnable, StrOutputParser())
        run_chain(chain, {"q":"你好"})  -> "A:Q:你好"

    思路:
        to_text = RunnableLambda(lambda v: v.to_string() if hasattr(v, "to_string") else str(v))
        return prompt | to_text | model_runnable | parser
    """
    # TODO: prompt | to_text(把 PromptValue 转 str) | model_runnable | parser
    ...


# ========== §30.5 执行:run_chain ==========


def run_chain(chain, variables: dict) -> str:
    """
    【执行 · §30.5】把 variables 喂进链子,拿最终输出。
    chain.invoke 会按顺序:prompt 渲染 → model 调用 → parser 解析。

    示例:
        run_chain(chain, {"q": "你好"})  -> "回复:回答:你好"

    思路:
        return chain.invoke(variables)
    """
    # TODO: chain.invoke(variables)
    ...


# ========== §30.6 对话记忆:append_turn ==========


def append_turn(history: list[dict], user: str, assistant: str) -> list[dict]:
    """
    【记忆 · §30.6】往对话历史追加一轮 user/assistant(不修改原 history)。
    LangChain 有 RunnableWithMessageHistory 自动管记忆,这里手写理解原理:
    记忆 = 维护一个 messages 列表,每轮追加,下次请求带上。

    示例:
        append_turn([], "你好", "你好呀")
            -> [{"role":"user","content":"你好"},{"role":"assistant","content":"你好呀"}]

    思路(和 Ch28 build_messages 一个道理,别 mutate 入参):
        return [*history, {"role":"user","content":user}, {"role":"assistant","content":assistant}]
    """
    # TODO: 返回 history 副本 + 追加 user 和 assistant 两条
    ...


# ---------------------------------------------------------------------
if __name__ == "__main__":
    p = build_prompt("Q:{q}")
    model = as_runnable(lambda s: f"A:{s}")
    chain = build_chain(p, model, StrOutputParser())
    print(run_chain(chain, {"q": "你好"}))
