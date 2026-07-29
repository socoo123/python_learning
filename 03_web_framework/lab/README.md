# 🎓 考试系统 Lab(M3 毕业项目)

> 综合实战:用 FastAPI + SQLAlchemy + JWT 搭一个**线上历史题考试系统**。
> 综合运用 Ch16(依赖注入)+ Ch19(SQLAlchemy)+ Ch21(JWT)+ Ch20(测试)。

---

## 一、系统概述

线上考试系统,三类用户:**管理员 / 老师 / 考生**。历史题考试(避开公式渲染),支持选择题(单选+多选)、填空题、问答题、分析题。

**核心流程**:
```
管理员:建考试 → 出题(4题型)→ 导入考生名单(分配准考号)→ 发布考试
考生:  准考号+密码登录 → 规定时间开考 → 作答 → 交卷(选择题自动判分)
       [考试结束]
老师:  看待批改作答 → 批改人工题给分+批注(已批改锁)→ ...
管理员:发布成绩
考生:  登录查分(仅发布后可见)
```

---

## 二、角色与权限(3 角色)

| 角色 | 能做 | 限制 |
|------|------|------|
| **管理员 admin** | 建考试、出题、导入考生名单(分配准考号)、发布考试、发布成绩 | 不参与作答/批改 |
| **老师 teacher** | 登录系统;考试结束后批改人工题(填空/问答/分析)给分+批注 | 不能出题/建考试;考试进行中不能批改 |
| **考生 student** | 准考号+密码登录;规定时间开考作答;交卷;成绩发布后查自己分数 | 不能看题库/他人分数;改前不能查分 |

---

## 三、题型与评分

| 题型 | 评分 | 数据 |
|------|------|------|
| 单选 single | **系统自动**(交卷即算) | 题目有选项,1 个正确;考生选 1 个 |
| 多选 multi | **系统自动**(全选对才得分) | 题目有选项,N 个正确;考生选多个 |
| 填空 fill | 老师批改(有参考答案) | 多个空,每空参考答案;考生填文本 |
| 问答 essay | 老师批改 + 批注 | 考生写文本 |
| 分析 analysis | 老师批改 + 批注 | 考生写文本(较长) |

---

## 四、关键业务规则

1. **准考号**:管理员导入名单时**预分配**,考生用「准考号 + 初始密码」登录激活。
2. **考试时间**:有**时间窗口**(start_time ~ end_time)+ **单次时长**(duration_minutes,开考后 N 分钟到时自动交卷)。
3. **成绩发布**:**整场考试**所有人工题批改完 → 管理员点「发布成绩」→ 所有考生同时可查(公平)。
4. **批改锁**:一道人工题被某老师批改后**标记**,其他老师看到不能再改(防并发冲突)。
5. **查分**:仅当考试状态 = `published`(成绩已发布)时,考生才能查;否则提示「未发布」。
6. **无邮件**:只支持登录查分(不发邮件,无 SMTP 依赖)。

---

## 五、数据模型(ER)

### 实体(7 个)

```
User(用户)
  id, username, password_hash, role[admin/teacher/student],
  name, admission_number(仅 student,全局唯一准考号)

Exam(考试)
  id, name, subject(历史), start_time, end_time, duration_minutes,
  status[draft/published/grading/published], total_score, created_by(admin_id)

Question(题目)
  id, exam_id, type[single/multi/fill/essay/analysis],
  content, score, order

Choice(选项,选择题用)
  id, question_id, content, is_correct

Enrollment(考生名单:考试↔考生)
  id, exam_id, student_id

Submission(考生答卷:一场考试一份)
  id, exam_id, student_id, start_time(开考时间),
  submit_time(交卷时间), status[in_progress/submitted], total_score

AnswerRecord(具体作答)
  id, submission_id, question_id,
  answer(选择题:选项id列表;人工题:文本),
  score, auto_scored[bool],
  graded_by(teacher_id), graded_at, feedback(批注)
```

### 关系

```
Exam 1—N Question 1—N Choice              (考试→题目→选项)
Exam N—N Student(经 Enrollment)            (一场考试多考生,一考生多场)
Exam 1—N Submission 1—N AnswerRecord      (考试→答卷→作答)
Student 1—N Submission                      (一考生多份答卷,每场一份)
Question 1—N AnswerRecord                   (一题被多个考生答)
```

### 状态机

**Exam.status**:
```
draft(出题中)→ published(已发布,可开考)→ grading(考试结束,批改中)→ published(成绩已发布)
   admin 发布       到 end_time 自动          所有改完 + admin 发布成绩
```

**Submission.status**:`in_progress`(开考中)→ `submitted`(已交卷 / 超时自动交卷)

---

## 六、实现里程碑

| 里程碑 | 目标 | 主要 API | 练的技术点 |
|--------|------|----------|-----------|
| **M0 骨架** | app + DB + JWT + 角色权限依赖 | 注册/登录(3 角色) | Ch16 依赖注入、Ch19 SQLAlchemy 基础、Ch21 JWT 多角色、`require_role` 依赖 |
| **M1 管理员** | 建考试 + 题库(4 题型)+ 导入名单 | 建考试/出题/加选项/导入考生 | 关系建模(一对多)、题型多态、嵌套 Pydantic、级联 |
| **M2 考生考试** | 开考/作答/交卷 + 自动判分 + 时间控制 | 开考/提交作答/交卷 | 状态机、事务(交卷算选择题分)、时间窗口+时长校验 |
| **M3 老师批改** | 看待批改、给分+批注、已批改锁 | 待批改列表/批改 | 权限隔离(只改人工题)、已批改标记防并发 |
| **M4 发布查分** | 发布成绩、考生查分 | 发布成绩/查分 | 状态扭转、聚合查询(总分)、权限(只查自己) |
| **M5 进阶(可选)** | 多选判分细节、超时自动交卷、成绩统计 | — | 复杂判分、后台任务、统计聚合 |

每个里程碑 = 一组 API + pytest 测试(TestClient + 内存 SQLite,复用 Ch19/Ch20 模式)。

---

## 七、技术栈(对应已学章节)

- **FastAPI**(Ch14/15):路由、Pydantic 模型、参数校验
- **SQLAlchemy 2.0**(Ch19):模型、关系、Session、查询
- **JWT + bcrypt**(Ch21):3 角色认证、`require_role` 权限依赖
- **依赖注入**(Ch16):`get_db`、`get_current_user`、`require_role("admin")`
- **pytest + TestClient**(Ch20):每里程碑配测试

---

## 八、进度

- [x] 需求确认(2026-07-23)
- [x] 数据模型设计
- [ ] M0 项目骨架
- [ ] M1 管理员(建考试/题库/名单)
- [ ] M2 考生(开考/作答/交卷/自动判分)
- [ ] M3 老师(批改/锁)
- [ ] M4 发布成绩/查分
- [ ] M5 进阶(可选)

---

> 本文档是设计 v1。实现过程中如有调整,在此更新。
