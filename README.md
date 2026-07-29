# 🐍 Python 全栈精通 — 面向 Java 老手的实战学习路径

> 15 年 Java 经验 → 一个月掌握 Python 的 Web 框架 / 运维脚本 / AI 框架 / LeetCode。
> 不是从 hello world 开始,而是**对比 Java + 实战驱动 + 测试验证**。

📖 **完整大纲请读 [SYLLABUS.md](./SYLLABUS.md)**（40 章 / 6 大模块）。

---

## 🎯 这是什么

一个为你（15 年 Java 后端）量身定制的 Python 精通项目。核心理念：

> **「测试通过 = 你掌握了」** —— 每个知识点都配一套作业和 pytest 测试用例,你写代码让测试全绿,就过关。

我们**跳过** hello world / 基础语法 / 变量定义（你 15 年经验不需要）,**聚焦**你最关心的四件事：
- ⭐ **Web 框架**（FastAPI，对比 Spring Boot）
- ⭐ **运维脚本**（Python 相对 Java 的舒适区）
- ⭐ **AI 框架**（LLM / RAG / Agent）
- ⭐ **LeetCode**（Pythonic 刷题，3 行顶 Java 15 行）

---

## 📂 目录结构

```
python_learning/
├── README.md                   ← 你在这里（学习指南）
├── SYLLABUS.md                 ← 详细大纲（40 章地图）
├── pyproject.toml              ← 项目配置 + pytest 配置
├── conftest.py                 ← 全局 pytest 工具（加载 mock 数据等）
│
├── 01_python_core/             ← M1：语言核心 (Ch01–07)
├── 02_stdlib/                  ← M2：标准库 (Ch08–12)
├── 03_web_framework/           ← M3：FastAPI (Ch13–22)
│   ├── app/  tests/  mock_data/
├── 04_devops_scripts/          ← M4：运维脚本 (Ch23–27)
├── 05_ai_framework/            ← M5：AI 框架 (Ch28–33)
├── 06_leetcode/                ← M6：LeetCode (Ch34–40)
│
├── assets/mock_data/           ← 共享 mock 数据（json）
└── tests/                      ← 全局测试
```

每一章学到时,会在对应模块目录下生成:
```
ch{NN}/
├── tutorial.md               ← 教程(费曼五步骨架)
├── ch{NN}_assignment.py      ← 你的作业(函数签名已给,你填实现)
├── test_ch{NN}_assignment.py ← 测试(pytest,全绿 = 掌握)
├── review.md                 ← 本章闪卡 + 复习日程
└── mock_data/*.json          ← 该章模拟数据
```

---

## 🚀 快速开始

### 1. 搭环境（Ch01 会详细讲，这里先跑通）
```bash
cd /Users/zy/ai_learn/python_learning

# 用 uv 一键装好依赖（自动建 .venv，读 pyproject.toml + uv.lock）
uv sync
# 后续命令都用 uv run，无需手动 source activate
```

### 2. 验证机制跑通
```bash
uv run pytest -v
```
看到绿条（passed）就说明测试基础设施 OK。

### 3. 开始学习
Ch01–Ch12 的五件套已就位（M1 语言核心 + M2 标准库），直接打开对应章节的 `tutorial.md` 开始。后续章节你说「**学 ChXX**」，我在对应模块目录生成该章的教程+作业+测试。你读完教程 → 写作业 → `uv run pytest` 跑绿 → 进入下一章。

---

## 🔄 学习工作流

**章间(宏观)**:你说「学 ChXX」→ 我生成五件套 → 你按「费曼五步」学完一整章 → 全绿 + 费曼讲清 → 下一章。

**章内(微观)**:见下方「费曼五步循环」表。

**随时可以**：
- 「讲得更细」—— 我展开某个知识点
- 「加练习题」—— 多给几道同类型作业
- 「这个 Java 里怎么写的」—— 我给 Java 对照
- 「这章太简单跳过」—— 直接进下一章

---

## 🧠 学习方法:费曼五步循环(基于《Ultralearning》)

> 你的计划已命中 Ultralearning 的「提取 + 反馈 + 直接性」(pytest + 实战),但 **测试通过 ≠ 真懂**。
> 加上下面这步,让碎片化学习也能真正留下东西。

**宏观**:你说「学 ChXX」→ 我生成五件套 → 你按五步学 → 全绿 + 费曼讲清 → 下一章

**微观(每章内部,约 40-60 分钟)**:

| 步 | 动作 | 对应原则 | 时长 |
|----|------|----------|------|
| ① 预览猜 | 看标题,猜「这和 Java 哪里不同」 | 元学习 | 30秒 |
| ② 先动手 | 先看作业试着写,卡住才读教程 | 直接性 | — |
| ③ 提取+反馈 | 合上教程凭记忆写 → `pytest` 红绿 | 提取·反馈 | 核心 |
| ④ **费曼** | 用一句话向「Java 同事」解释本章核心 | 直觉 | 2分钟 |
| ⑤ **存闪卡** | 记 1 张卡到 [`REVIEW.md`](./REVIEW.md),标 1/3/7 天复习 | 记忆留存 | 1分钟 |

> ③ 你已经在做。**④⑤ 是关键补丁**——防止「测试绿了但两周后全忘」。每章 `tutorial.md` 有费曼题、`review.md` 有闪卡。

---

## 🟢🟡🔴 Java 老手阅读标记

教程正文里用这三色帮你跳读：

| 标记 | 含义 | 处理 |
|------|------|------|
| 🟢 | Java 老手秒懂（和 Java 几乎一样） | 扫一眼 |
| 🟡 | 注意差异（名字像但行为不同） | 仔细看 |
| 🔴 | Python 特有（Java 完全没有） | **重点学** |

---

## 📅 30 天节奏建议

| 周 | 内容 | 章节 |
|----|------|------|
| 第 1 周 | 语言核心（打地基） | Ch01–07 |
| 第 2 周 | 标准库 + Web 前半 | Ch08–17 |
| 第 3 周 | 异步/DB/运维 | Ch18–27 |
| 第 4 周 | AI + LeetCode | Ch28–40 |

---

## ❓ 为什么选 FastAPI 而不是 Django/Flask

| | FastAPI | Flask | Django |
|---|---|---|---|
| 类型注解 | ✅ 原生（Java 老手爽） | ❌ | 部分 |
| 异步 | ✅ 原生 | ⚠️ | 部分 |
| 学习曲线 | 中 | 低 | 高 |
| 自动文档 | ✅ | 需插件 | 需配置 |
| 2024+ 新项目 | **首选** | 经典 | 大而全 |

→ 本课程**以 FastAPI 为主**（Ch14–21），Flask/Django 在 Ch22 对比介绍。你掌握了 FastAPI,Flask/Django 迁移成本很低。

---

**👉 准备好了就说「我要学 Ch01」,我们开始！**
