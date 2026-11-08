# 页面二「智能问答」模块接口契约（Lead 制定，禁止改动本文件语义）

本文件定义页面二并行开发的三个模块边界。**所有实现必须严格遵循本文件的数据结构**，
这样 `views/qa.py`（Lead 负责）可以在模块未完成时先按契约开发。

写作用域（不要越界写别的文件）：

| 模块 | 负责人 | 允许写 |
| --- | --- | --- |
| `core/policy.py` | policy-kb | 仅 `core/policy.py` |
| `core/pdf_reader.py`、`tools/**`、`docs/samples/**` | pdf-engine | 仅这些路径 |
| `core/kb.py`、`core/ai.py`、`core/state.py` | retrieval-core | 仅这三个文件 |
| `views/qa.py`、`stop.bat/ps1`、README | Lead | 其余 |

公共约定：Python 3.12、纯标准库优先（不新增第三方依赖）、全部面向中文用户、
文案与既有项目保持一致（演示数据必须能看出是演示，不冒充学校官方系统）。
所有数据为「河南大学」演示数据，文号/制度名可虚构，但要标注「（演示）」。

---

## 1. `core/policy.py`（policy-kb）

提供校园制度库、通知、资助政策、快捷问题、常见问题、四年规划。全部为模块级常量。

### 1.1 `POLICY_DOCS: list[dict]`

至少 10 篇制度文档，覆盖：学生证、资助体系、国家奖学金、助学贷款/助学金/勤工助学、
校园卡、学籍证明、请假、考试纪律、第二课堂、信息公开（通知查询）、学业规划、活动管理。

```python
{
  "id": "doc-student-id",                 # 唯一，doc- 前缀，全项目引用
  "title": "河南大学学生证管理办法（演示）",
  "doc_no": "校学〔2025〕12 号",
  "department": "学生处",
  "issued": "2025-09-01",                 # 发布日期 ISO 字符串
  "effective": "2025-09-01",
  "category": "学籍证件",                  # 学籍证件/资助奖助/教学教务/生活服务/活动实践/信息公开/成长规划
  "level": "校级规章",                     # 校级规章/部门办法/办事指南/年度通知
  "status": "现行有效",
  "applies_to": "全体全日制本科生",
  "summary": "一句话摘要，不超过 45 字",
  "keywords": ["学生证", "补办", "丢失", "挂失"],
  "sections": [                           # 3—6 条，供答案引用摘录
      {"clause": "第三章 第十一条", "text": "学生证遗失后，学生应在 3 个工作日内……"},
  ],
}
```

### 1.2 `CITATIONS_BY_KB: dict[str, list[str]]`

键 = **已有 `core/data.py` 中全部 12 个 QA_KB 条目的 id**：
`campus-card, library, scholarship, repair, course-selection, transcript, leave,
shuttle, activities, medical, empty-classroom, psychology`
加上 `KB_EXTRA` 中全部新条目 id。值 = `POLICY_DOCS` 中的 doc_id 列表（1—2 个，第一个为主来源）。
不允许出现未在 `POLICY_DOCS` 中定义的 id。

### 1.3 `KB_EXTRA: list[dict]`

与 `core/data.py:QA_KB` 完全同构的条目，另加两个字段：

```python
{
  "id": "student-id",
  "keywords": ["学生证", "补办", "丢了", "丢失", "挂失", "证件"],
  "question": "学生证丢了怎么办？",
  "title": "学生证丢失补办指南",
  "intro": "先线上挂失，再带材料到学生事务大厅补办，最快 1 个工作日。",
  "steps": ["立即在……", "……"],
  "tip": "……",
  "source": "河南大学学生证管理办法（演示）",
  "links": [["查看办事流程", "?page=services&q=学生证"], ["去个人事务中心", "?page=center"]],
  "tone": "blue",
  "citations": ["doc-student-id"],        # 新增
  "extras": [],                           # 新增：附加富内容，见下
}
```

必须包含以下 7 个条目，其中前 5 个与「预设快捷问题」一一对应，必须能被问题原文高分命中：

| id | question（原文必须一致） | extras |
| --- | --- | --- |
| `student-id` | `学生证丢了怎么办？` | `[]` |
| `aid-policies` | `有哪些学生资助政策？` | `["aid_policies"]` |
| `activities-latest` | `最近有哪些校园活动？` | `["activities"]` |
| `notices-query` | `如何查询学校最新通知？` | `["notices"]` |
| `life-plan` | `如何规划我的大学生活？` | `["plan"]` |
| `exam-rules` | `考试作弊会怎么处理？` | `[]` |
| `second-classroom` | `第二课堂学分怎么获得？` | `[]` |

`extras` 取值只允许：`"activities"`、`"aid_policies"`、`"notices"`、`"plan"`。

### 1.4 `NOTICES: list[dict]`（6—8 条最新通知）

```python
{
  "id": "notice-2026-1105-exam",
  "title": "关于 2026—2027 学年秋季学期期末考试安排的通知",
  "date": "2026-11-05",
  "department": "教务处",
  "category": "教务",                     # 教务/资助/活动/后勤/学工
  "tag": "重要",                          # 重要/置顶/普通
  "summary": "一句话，40 字内",
  "href": "?page=qa&q=期末考试怎么安排？",
  "doc_id": "doc-exam-rules",             # 可为 ""
  "source": "教务处官网 · 通知公告",
}
```

### 1.5 `AID_POLICIES: list[dict]`（6—8 项资助政策）

```python
{"name": "国家奖学金", "amount": "10000 元 / 年", "target": "二年级以上本科生",
 "deadline": "每年 9—10 月", "desc": "一句话说明", "tone": "gold", "doc_id": "doc-scholarship"}
```

### 1.6 `QUICK_QUESTIONS: list[dict]`（顺序固定，5 条）

```python
{"id": "q-student-id", "label": "学生证丢了怎么办？", "question": "学生证丢了怎么办？",
 "hint": "补办材料 + 办理地点", "icon": "id-card", "tone": "blue"}
```
顺序：学生证 → 学生资助政策 → 校园活动 → 最新通知 → 大学生活规划。
`label` 与 `question` 文本必须一致（页面按钮直接展示 label）。

### 1.7 `FAQ_RECOMMENDED: list[dict]`（8—10 条，常见问题推荐）

```python
{"question": "校园卡丢了怎么补办？", "tag": "生活服务", "hot": True}
```
须覆盖政策/流程/生活三类，并与已有 QA_KB 或 KB_EXTRA 的问题能命中。

### 1.8 `PLAN_STAGES: list[dict]`（大一—大四）

```python
{"stage": "大一", "title": "打地基：适应 + 探索", "focus": "学业适应、社团试水",
 "items": ["……", "……"], "tone": "blue"}
```

---

## 2. `core/pdf_reader.py`（pdf-engine）

纯标准库 PDF 文本提取。API：

```python
def is_pdf(data: bytes) -> bool: ...
def decode_text_file(data: bytes) -> str: ...   # .txt/.md 上传，utf-8-sig → utf-8 → gbk 兜底

def extract(data: bytes, max_pages: int = 30, max_chars: int = 200000) -> dict:
    """永不抛异常。返回：
    {
      "ok": bool,
      "engine": "pdf" | "none",
      "pages": [{"no": 1, "text": "第 1 页正文……"}],
      "page_count": int,        # 实际解析到的页数（≥ len(pages)）
      "chars": int,             # 提取到的正文字符数
      "encrypted": bool,
      "scanned": bool,          # 无可用文本层（扫描件）时为 True
      "warnings": [str],
      "error": "",              # ok=False 时给用户看的一句话中文原因
    }
    """
```

要求：

- 支持 `FlateDecode`（zlib）、未压缩流；对象流 `ObjStm`、交叉引用流可忽略但不得崩溃；
  通过扫描 `N G obj ... endobj` 兜底解析（不依赖 xref 偏移）。
- 支持文本操作符 `Tj`、`TJ`、`'`、`"`，`Td/TD/T*/Tm/TL` 产生的换行。
- 中文关键：解析 **ToUnicode CMap**（`bfchar`/`bfrange`，含 `beginbfrange` 区间与 UTF-16 代理对），
  以及 CID 字体 Identity-H；WinAnsi/MacRoman 简单编码兜底。目标：真实 Word/浏览器导出的
  中文 PDF 能正确提取出中文，而不是乱码或 CID 数字。
- 清理控制字符、压缩连续空白、按页组织；`scanned=True` 时 `pages` 可为空、`ok=True` 但 `chars=0`。
- 单个文件 50MB / 30 页 / 20 万字符上限内快速返回（<2s）。

`tools/test_pdf_reader.py`：自测脚本，`python tools/test_pdf_reader.py` 输出逐项 PASS/FAIL
并 `sys.exit(非 0)` 表示失败。覆盖：中文 PDF 真实文件、英文 PDF、空字节、乱码 PDF、
`decode_text_file` 的 utf-8/GBK、超页数截断。

`docs/samples/`：提供 2 个可直接用于演示上传的中文 PDF（2—3 页，<300KB），
例如 `docs/samples/学生证管理办法（演示）.pdf`、`docs/samples/学生资助政策手册（演示）.pdf`。
建议用本机 Edge 无头打印 HTML 生成：`msedge --headless=new --disable-gpu
--print-to-pdf="out.pdf" --no-pdf-header-footer "file:///...html"`，并在测试中证明
`extract()` 能取到正确中文。

---

## 3. `core/kb.py` / `core/ai.py` / `core/state.py`（retrieval-core）

### 3.1 `core/kb.py`

```python
def answer(question: str, history: list[dict] | None = None,
           uploads: list[dict] | None = None) -> dict
```

`history` 为 `st.session_state` 中的消息列表：`{"role": "user"|"assistant", "content": str|dict}`。
`uploads` 为已上传资料列表（由 `make_upload` 生成）。

返回结构（`views/qa.py` 严格按此渲染，**缺失字段用默认值**也可，但不要改名）：

```python
{
  "matched": True,
  "intent": "student-id",                 # 命中的条目 id / "upload" / "" / "greeting"
  "intent_label": "学籍证件",              # 页面上展示的中文短标签
  "title": "学生证丢失补办指南",
  "intro": "……",
  "steps": ["……", "……"],
  "tip": "……",
  "tone": "blue",                          # blue/teal/gold/violet/rose
  "confidence": 0.86,                      # 0—1；None 表示不展示
  "citations": [                           # 答案来源引用（必须）
     {"doc_id": "doc-student-id", "title": "河南大学学生证管理办法（演示）",
      "doc_no": "校学〔2025〕12 号", "department": "学生处", "issued": "2025-09-01",
      "clause": "第三章 第十一条", "excerpt": "……", "status": "现行有效",
      "source_type": "policy"}             # policy | upload
  ],
  "links": [["去办事流程导航", "?page=services"]],
  "attachments": [                         # 富内容附件（可空）
     {"type": "list", "title": "本周校园活动",
      "items": [{"icon": "compass", "tone": "gold", "title": "……", "meta": "11 月 14 日 · 金明校区",
                 "desc": "……", "tag": "科技", "href": "?page=activities"}]},
     {"type": "timeline", "title": "四年规划建议",
      "items": [{"step": "大一", "title": "打地基", "desc": "……", "meta": "……", "tone": "blue"}]}
  ],
  "suggestions": ["……", "……", "……"],        # 继续追问建议（3 条）
  "retrieval": [                           # 知识库检索轨迹（必须）
     {"source": "policy", "title": "河南大学学生证管理办法（演示）",
      "snippet": "……", "score": 0.91, "meta": "学生处 · 校学〔2025〕12 号", "doc_id": "doc-student-id"}
  ],
  "context_used": False,                    # 本轮是否用了上文（连续对话）
  "raw_question": "……",
  "elapsed_ms": 8,
}
```

`search`：

```python
def search(query: str, limit: int = 6, uploads: list[dict] | None = None) -> list[dict]:
    # 返回 [{source, id, doc_id, kb_id, title, snippet, score, meta, question}]
    # source: policy | faq | upload；question 为可直接提问的整句（可空）
```

`make_upload`：

```python
def make_upload(name: str, extracted: dict) -> dict:
    # {"id": "upload-...", "name": "xxx.pdf", "pages": 3, "chars": 1200,
    #  "chunks": [{"page": 1, "text": "……"}], "added_at": "2026-11-07 12:00"}
```

其它：

- `def followups(result) -> list[str]`：基于命中条目生成 3 条追问。
- 检索实现：中文按 2-gram + 关键词加权（数据层 `keywords` 字段权重高），归一化到 0—1。
  纯 Python，不引入依赖。
- **连续对话**：当本轮问题是短追问（如「那要带什么材料？」「多久能办好？」「在哪里办？」
  「需要预约吗」「然后呢」），结合 `history` 里上一轮命中的条目，返回该条目的对应字段
  （材料/时限/地点/注意），`context_used=True`，`intent` 沿用上一轮，标题可写成
  「接着上一个问题 · 学生证补办」。必须真正改变回答内容，不能只是重复上一轮。
- 快捷问题原文必须精确命中对应 KB 条目（`student-id`、`aid-policies`、
  `activities-latest`、`notices-query`、`life-plan`），并带 `extras` 附件。
- 上传资料命中：当上传片段相关度最高时，`intent="upload"`，标题「根据你上传的资料」，
  `citations` 里给出 `source_type="upload"`、`file`、`page`、`excerpt`；连续对话同样生效。
- 任何异常都要 `try/except` 兜底成 fallback 答案（`matched=False`，给出检索建议），绝不抛出。

### 3.2 `core/ai.py`

保留旧接口，供 `views/home.py` 使用：`answer(question) -> dict` 旧字段
（`title/intro/steps/tip/source/links/tone/confidence/suggestions/raw_question/matched/entry_id`）
必须继续存在，`source` 用 citations[0].title 填充；可委托 `kb.answer`，额外字段原样透传。

### 3.3 `core/state.py`

保留现有函数与字段（`init_state/get_todos/todo_progress/toggle_todo/handle_toggle_param/
registrations/register_activity/is_registered/qa_history/append_qa/clear_qa`），新增：

```python
def qa_docs() -> list[dict]: ...                    # 当前会话已上传资料
def qa_add_doc(doc: dict) -> None: ...              # 去重（同名覆盖），最多 5 份
def qa_remove_doc(doc_id: str) -> None: ...
def qa_clear_docs() -> None: ...
def qa_new_session() -> str: ...                    # 清空问答+资料，返回新会话 id
def qa_session_no() -> int: ...
def qa_last_result() -> dict | None: ...             # 最后一条 assistant 的 dict
def qa_persist() -> None: ...                       # 见下
def qa_restore() -> None: ...
```

- `append_qa` / `clear_qa` / `qa_add_doc` / `qa_remove_doc` 之后自动调用 `qa_persist()`。
- 持久化到 `.tmp/qa_session.json`（相对项目根）：消息（最多 30 条，assistant 的 dict 里
  `retrieval` 只留前 6 条、`attachments` 最多 2 个）+ 上传资料（`chunks` 总字符上限 60k），
  UTF-8、`tmp` 文件 + `os.replace` 原子写、`try/except` 忽略一切 IO 错误。
- `qa_restore()` 在 `init_state()` 里调用：仅当 `qa_messages` 为空时从磁盘恢复，
  这样刷新页面、跳转其它页面再回来，对话仍在（演示友好）。`qa_new_session()` 清空磁盘记录。

---

## 4. 验收口径（Lead 集成后统一执行）

1. `python -m compileall core views app.py` 通过。
2. 5 个快捷问题每个都能得到结构不同、内容对应的答案：
   学生证（补办流程）/ 资助（政策清单）/ 活动（活动列表）/ 通知（通知列表）/ 规划（四年时间线）。
3. 连续对话：先问「学生证丢了怎么办？」，再问「那要带什么材料？」，第二答必须有上文承接。
4. 上传 `docs/samples/*.pdf` 后提问文件内容，答案引用显示「上传文件 · 第 N 页」。
5. 每个回答都能展开「依据来源」，含制度名、文号、条款、摘录。
6. 知识库检索面板搜索「奖学金」，返回相关制度/FAQ 且可一键提问。
7. 浏览器 1440px / 390px 无横向溢出、0 console error。
