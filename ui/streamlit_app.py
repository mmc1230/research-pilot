import requests
import streamlit as st


st.set_page_config(page_title="ResearchPilot 科研助理", page_icon="RP", layout="wide")

API_BASE = "http://127.0.0.1:8000"


st.markdown(
    """
    <style>
    :root {
        --rp-ink: #172033;
        --rp-muted: #637083;
        --rp-line: #d9e1ea;
        --rp-accent: #1677ff;
        --rp-soft: #eef6ff;
        --rp-good: #0f8a5f;
    }
    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 2rem;
        max-width: 1240px;
    }
    section[data-testid="stSidebar"] {
        background: #f7f9fc;
        border-right: 1px solid var(--rp-line);
    }
    h1, h2, h3 {
        color: var(--rp-ink);
        letter-spacing: 0;
    }
    .rp-hero {
        border: 1px solid var(--rp-line);
        border-radius: 8px;
        padding: 22px 24px;
        background: linear-gradient(180deg, #ffffff 0%, #f6fbff 100%);
        margin-bottom: 18px;
    }
    .rp-title {
        font-size: 34px;
        line-height: 1.15;
        font-weight: 760;
        color: var(--rp-ink);
        margin-bottom: 8px;
    }
    .rp-subtitle {
        font-size: 15px;
        color: var(--rp-muted);
        max-width: 840px;
    }
    .rp-card {
        border: 1px solid var(--rp-line);
        border-radius: 8px;
        background: #ffffff;
        padding: 16px 18px;
        min-height: 116px;
    }
    .rp-card-title {
        font-weight: 700;
        color: var(--rp-ink);
        margin-bottom: 6px;
    }
    .rp-card-copy {
        color: var(--rp-muted);
        font-size: 14px;
    }
    .rp-step {
        border-left: 3px solid var(--rp-accent);
        background: var(--rp-soft);
        padding: 10px 12px;
        border-radius: 6px;
        color: var(--rp-ink);
        font-size: 14px;
        margin: 8px 0;
    }
    .rp-kpi {
        border: 1px solid var(--rp-line);
        border-radius: 8px;
        padding: 14px;
        background: #ffffff;
    }
    .rp-kpi-value {
        font-size: 24px;
        font-weight: 760;
        color: var(--rp-accent);
    }
    .rp-kpi-label {
        color: var(--rp-muted);
        font-size: 13px;
    }
    div.stButton > button {
        border-radius: 6px;
        border: 1px solid #1268df;
        background: #1677ff;
        color: white;
        font-weight: 650;
        min-height: 40px;
    }
    div.stButton > button:hover {
        border-color: #0f5ec7;
        background: #0f6be8;
        color: white;
    }
    div[data-testid="stFileUploader"] {
        border: 1px dashed #a8bdd5;
        border-radius: 8px;
        padding: 8px;
        background: #fbfdff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_get(endpoint: str, timeout: int = 30):
    response = requests.get(f"{API_BASE}{endpoint}", timeout=timeout)
    response.raise_for_status()
    return response.json()


def api_post(endpoint: str, payload: dict, timeout: int = 120):
    response = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def post_file(endpoint: str, uploaded_file, timeout: int = 180):
    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
    response = requests.post(f"{API_BASE}{endpoint}", files=files, timeout=timeout)
    response.raise_for_status()
    return response.json()


def status_badge() -> None:
    try:
        health = api_get("/health", timeout=3)
        st.sidebar.success(f"后端已连接：{health['app']}")
    except Exception:
        st.sidebar.error("后端未连接，请先启动 FastAPI")


def render_hero() -> None:
    st.markdown(
        """
        <div class="rp-hero">
            <div class="rp-title">ResearchPilot 科研助理 Agent</div>
            <div class="rp-subtitle">
                面向论文阅读、代码项目理解和实验结果分析的科研工作台。
                系统会把上传资料转成 chunks，生成 embedding，写入向量库，再通过 LangGraph 工作流进行检索、工具调用、回答生成和证据校验。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline() -> None:
    st.markdown("#### RAG 入库流程")
    cols = st.columns(4)
    steps = [
        ("1. 解析文件", "PDF 抽取页面文本；Markdown、txt、代码文件直接读取。"),
        ("2. 切分 Chunk", "用 LangChain splitter 按语义边界和长度切分。"),
        ("3. 生成 Embedding", "默认离线 hash embedding，也可切换 OpenAI Embeddings。"),
        ("4. 写入向量库", "Chunks 和元信息进入 Chroma，SQLite 保存文件与日志。"),
    ]
    for col, (title, copy) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class="rp-card">
                    <div class="rp-card-title">{title}</div>
                    <div class="rp-card-copy">{copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def show_ingest_result(result: dict) -> None:
    st.success(f"入库完成，source_id = {result.get('document_id')}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="rp-kpi"><div class="rp-kpi-value">{result.get("chunk_count", "-")}</div><div class="rp-kpi-label">Chunks</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="rp-kpi"><div class="rp-kpi-value">{result.get("doc_type", "paper")}</div><div class="rp-kpi-label">资料类型</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="rp-kpi"><div class="rp-kpi-value">{result.get("document_id", "-")}</div><div class="rp-kpi-label">Source ID</div></div>',
            unsafe_allow_html=True,
        )
    with st.expander("查看入库元数据"):
        st.json(result)


def documents_table() -> list[dict]:
    try:
        docs = api_get("/documents")
    except Exception as exc:
        st.error(f"读取资料列表失败：{exc}")
        return []
    if docs:
        st.dataframe(
            docs,
            use_container_width=True,
            column_config={
                "id": "Source ID",
                "filename": "文件名",
                "doc_type": "类型",
                "chunk_count": "Chunks",
                "collection_name": "向量集合",
                "created_at": "创建时间",
            },
            hide_index=True,
        )
    else:
        st.info("还没有入库资料。")
    return docs


st.sidebar.markdown("## ResearchPilot")
status_badge()
API_BASE = st.sidebar.text_input("后端地址", value=API_BASE)
page = st.sidebar.radio(
    "功能导航",
    ["总览", "资料入库", "论文阅读", "代码项目", "实验 CSV", "智能问答", "资料与日志"],
)
st.sidebar.caption("当前版本：本地 RAG + LangGraph + MCP 风格工具")

render_hero()

if page == "总览":
    render_pipeline()
    st.markdown("#### 核心能力")
    c1, c2, c3 = st.columns(3)
    cards = [
        ("论文阅读", "上传 PDF 后建立向量索引，支持基于证据片段回答创新点、方法、实验设置和结论。"),
        ("代码理解", "扫描本地项目目录，过滤无关文件，索引核心代码，辅助理解架构、入口和调用链。"),
        ("实验分析", "读取 CSV，识别指标列，自动比较模型表现、异常点和可写入论文的结果分析。"),
    ]
    for col, (title, copy) in zip([c1, c2, c3], cards):
        with col:
            st.markdown(
                f"""
                <div class="rp-card">
                    <div class="rp-card-title">{title}</div>
                    <div class="rp-card-copy">{copy}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("#### 已入库资料")
    documents_table()

elif page == "资料入库":
    st.markdown("## 资料入库与向量化")
    render_pipeline()
    st.markdown(
        '<div class="rp-step">RAG 不需要训练大模型。这里的“训练资料”更准确地说是：把你的文件向量化并建立检索索引。</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "上传 PDF、Markdown、txt、代码或配置文件",
        type=["pdf", "md", "txt", "py", "cpp", "c", "h", "hpp", "yaml", "yml", "json", "toml"],
    )
    if uploaded and st.button("开始入库并生成 Embedding", use_container_width=True):
        with st.spinner("正在解析、切分、生成 embedding 并写入向量库..."):
            try:
                show_ingest_result(post_file("/upload/document", uploaded))
            except Exception as exc:
                st.error(f"入库失败：{exc}")

elif page == "论文阅读":
    st.markdown("## 论文阅读")
    left, right = st.columns([0.95, 1.05])
    with left:
        paper = st.file_uploader("上传 PDF 论文", type=["pdf"])
        if paper and st.button("建立论文索引", use_container_width=True):
            with st.spinner("正在抽取论文文本并建立向量索引..."):
                try:
                    show_ingest_result(post_file("/upload/paper", paper))
                except Exception as exc:
                    st.error(f"论文入库失败：{exc}")
    with right:
        st.markdown("#### 推荐问题")
        for q in [
            "这篇论文的核心创新是什么？",
            "这篇论文的方法流程是什么？",
            "这篇论文的实验设置和评价指标是什么？",
            "这篇论文对我的研究有什么可借鉴之处？",
        ]:
            st.code(q, language=None)

elif page == "代码项目":
    st.markdown("## 代码项目理解")
    project_path = st.text_input("本地项目路径", placeholder="例如：D:/Projects/my-research-code")
    max_files = st.slider("最多索引文件数", min_value=20, max_value=300, value=80, step=10)
    if project_path and st.button("扫描并索引项目", use_container_width=True):
        with st.spinner("正在扫描目录、摘要代码文件并建立代码向量索引..."):
            try:
                result = api_post("/project/scan", {"project_path": project_path, "max_files": int(max_files)}, timeout=240)
                st.success(f"项目索引完成，source_id = {result['project_id']}")
                k1, k2, k3 = st.columns(3)
                k1.metric("源文件数", result["file_count"])
                k2.metric("已索引文件", result["indexed_files"])
                k3.metric("Source ID", result["project_id"])
                st.markdown("#### 项目结构")
                st.code(result["tree"], language="text")
                with st.expander("查看文件摘要"):
                    st.json(result["summaries"])
            except Exception as exc:
                st.error(f"项目扫描失败：{exc}")

elif page == "实验 CSV":
    st.markdown("## 实验结果分析")
    csv_file = st.file_uploader("上传实验结果 CSV", type=["csv"])
    if csv_file and st.button("读取并分析 CSV", use_container_width=True):
        with st.spinner("正在识别字段、指标列、最优结果和异常点..."):
            try:
                result = post_file("/upload/csv", csv_file)
                st.success(f"CSV 已保存，source_id = {result['document_id']}")
                schema = result["schema"]
                analysis = result["analysis"]
                c1, c2, c3 = st.columns(3)
                c1.metric("行数", schema["rows"])
                c2.metric("列数", len(schema["columns"]))
                c3.metric("指标列", len(schema["metric_columns"]))
                st.markdown("#### 检测到的指标列")
                st.write(schema["metric_columns"])
                st.markdown("#### 最优结果")
                st.json(analysis["best_by_metric"])
                with st.expander("完整 Schema 与分析结果"):
                    st.json(result)
            except Exception as exc:
                st.error(f"CSV 分析失败：{exc}")

elif page == "智能问答":
    st.markdown("## 智能问答")
    docs = documents_table()
    source_labels = {"paper": "论文", "project": "代码项目", "csv": "实验结果", "general": "通用科研问题"}
    source_type = st.selectbox("知识源类型", options=list(source_labels.keys()), format_func=lambda x: source_labels[x])
    source_id = st.text_input("Source ID", placeholder="从上方资料表中复制 id")
    question = st.text_area("问题", height=130, placeholder="例如：这个项目的整体架构是什么？或：哪个模型的 RMSE 最低？")
    examples = {
        "paper": ["这篇论文的核心创新是什么？", "这篇论文的方法流程是什么？", "实验设置是什么？"],
        "project": ["这个项目的整体架构是什么？", "主要入口文件在哪里？", "如果我要复现实验，应该从哪个文件开始？"],
        "csv": ["哪个模型整体表现最好？", "是否存在 R2 高但 RMSE 不占优的情况？", "这个结果如何写成论文中的结果分析？"],
        "general": ["请帮我把这个研究问题拆成实验计划。"],
    }
    st.caption("示例问题：" + "；".join(examples[source_type]))
    if question and st.button("运行 Agent 工作流", use_container_width=True):
        with st.spinner("正在路由意图、检索证据、调用工具并生成回答..."):
            try:
                result = api_post(
                    "/chat",
                    {"question": question, "source_type": source_type, "source_id": source_id or None},
                    timeout=240,
                )
                st.markdown("### 回答")
                st.markdown(result["answer"])
                if result.get("warnings"):
                    st.warning("\n".join(result["warnings"]))
                with st.expander("引用片段 / 证据"):
                    st.json(result.get("citations", []))
                with st.expander("Agent 工作流日志"):
                    st.json(result.get("logs", []))
                st.caption(f"session_id = {result['session_id']}")
            except Exception as exc:
                st.error(f"问答失败：{exc}")

else:
    st.markdown("## 资料与日志")
    docs = documents_table()
    st.markdown("#### 会话日志")
    session_id = st.text_input("Session ID")
    if session_id and st.button("查询日志"):
        try:
            st.json(api_get(f"/logs/{session_id}"))
        except Exception as exc:
            st.error(f"日志查询失败：{exc}")
