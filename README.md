# ResearchPilot 科研助理 Agent

ResearchPilot 是一个面向科研工作的智能 Agent 原型，聚焦三个核心场景：论文阅读、代码项目理解和实验结果分析。

它不是一个简单的 LLM API 套壳，而是一个具备完整工程结构的 Agent 系统：包含 RAG 知识库、LangChain 文档处理流程、LangGraph 多节点工作流、MCP 风格本地工具封装、SQLite 日志存储、FastAPI 后端接口和 Streamlit 中文前端。

## 核心功能

- 论文阅读：上传 PDF，抽取文本，切分 chunk，建立向量索引，并基于论文证据回答问题。
- 通用资料入库：支持 PDF、Markdown、txt、代码文件和配置文件；系统会自动切分、生成 embedding，并写入 Chroma 向量库。
- 代码项目理解：扫描本地代码目录，过滤无关文件，摘要核心代码，识别主要模块、类和函数。
- 实验结果分析：上传 CSV，识别字段类型、缺失值、常见指标列，并自动分析模型表现、最优结果和异常点。
- Agent 工作流：使用 LangGraph 对问题进行意图识别、检索、工具路由、工具执行、回答生成和证据校验。
- 证据与日志：回答中保留引用片段或工具结果，工具调用与会话记录写入 SQLite，便于调试。

## RAG 不是训练

上传文件后，ResearchPilot 不会训练或微调大模型。这里发生的是 RAG 入库流程：

```text
文件 -> 文本抽取 -> chunk 切分 -> embedding 向量化 -> 写入向量库 -> 检索相关片段 -> 基于证据生成回答
```

也就是说，你的论文、代码和实验文件会被转成可检索的知识。LLM 本身不会因为上传文件而改变参数。真正的 fine-tuning 或模型训练可以作为后续独立功能扩展。

## 技术架构

- 后端：Python、FastAPI
- Agent 编排：LangGraph
- 文档处理：LangChain loaders / splitters
- RAG：Chroma 向量库
- Embedding：OpenAI Embeddings，或离线 deterministic fake embedding
- 工具调用：MCP 风格本地 Tool Registry
- 数据处理：pandas、pypdf
- 存储：SQLite
- 前端：Streamlit 中文工作台

## 项目结构

```text
research_pilot/
  app/
    main.py                 # FastAPI 入口
    config.py               # 配置与环境变量
    api/                    # API 路由
    agents/                 # LangGraph 工作流
    rag/                    # 文档加载、切分、embedding、向量库、检索
    tools/                  # MCP 风格本地工具
    services/               # 业务服务层
    storage/                # SQLite 存储
  ui/
    streamlit_app.py        # Streamlit 中文前端
  data/
    uploads/                # 上传文件
    vector_db/              # Chroma 向量库
    projects/               # 项目数据目录
  tests/                    # 单元测试
  requirements.txt
  README.md
  .env.example
```

## 安装方法

进入项目目录：

```powershell
cd D:\Projects\rag-agent\research_pilot
```

创建虚拟环境：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

如果默认 `python` 版本太旧，可以指定 Python 3.10+。例如本机 Python 3.13：

```powershell
D:\Python\python3.13.5\python.exe -m venv .venv
.\.venv\Scripts\python.exe -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
copy .env.example .env
```

## 环境变量

默认可以离线运行基础流程：

```env
EMBEDDING_PROVIDER=fake
```

这种模式会使用确定性的本地 hash embedding，适合开发、测试和流程演示。

如果希望使用 OpenAI 进行真实 embedding 和回答生成，修改 `.env`：

```env
OPENAI_API_KEY=your_key
EMBEDDING_PROVIDER=openai
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## 使用 DeepSeek 作为聊天模型

ResearchPilot 支持 DeepSeek 这类 OpenAI-compatible LLM API。DeepSeek 只用于聊天模型生成回答，RAG 的 embedding provider 单独配置。

`.env` 示例：

```env
EMBEDDING_PROVIDER=fake
OPENAI_API_KEY=your_deepseek_api_key
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-v4-pro
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

说明：

- `OPENAI_MODEL=deepseek-v4-pro` 是聊天模型配置。
- 不要把 `deepseek-v4-pro` 当作 embedding model 使用。
- `EMBEDDING_PROVIDER=fake` 只用于部署和流程测试，不会调用任何 embedding API。
- 只有当 `EMBEDDING_PROVIDER=openai` 时，系统才会调用 `OpenAIEmbeddings` 并读取 `OPENAI_EMBEDDING_MODEL`。
- 后续可以扩展 `EMBEDDING_PROVIDER=local_bge`，接入 `BAAI/bge-small-zh-v1.5`、`BAAI/bge-m3` 等本地 embedding 模型。

测试 DeepSeek API 是否连通：

```powershell
.\.venv\Scripts\python.exe scripts/test_deepseek_api.py
```

Linux / CentOS：

```bash
python scripts/test_deepseek_api.py
```

启动后端：

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 启动后端

```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

后端地址：

```text
http://127.0.0.1:8000
```

健康检查：

```text
http://127.0.0.1:8000/health
```

## 启动前端

```powershell
.\.venv\Scripts\streamlit.exe run ui/streamlit_app.py
```

前端默认地址：

```text
http://127.0.0.1:8501
```

如果端口被占用，可以指定端口：

```powershell
.\.venv\Scripts\streamlit.exe run ui/streamlit_app.py --server.port 8502
```

## 部署到 CentOS 服务器

项目已经提供 CentOS 部署模板：

```text
deploy/researchpilot-api.service
deploy/researchpilot-ui.service
deploy/nginx-researchpilot.conf
.env.production.example
docs/CENTOS_DEPLOY.md
```

完整部署流程见：

[CentOS 部署指南](docs/CENTOS_DEPLOY.md)

## 使用示例

### 上传论文

```powershell
curl -X POST -F "file=@paper.pdf" http://127.0.0.1:8000/upload/paper
```

### 上传通用资料并建立 RAG 索引

```powershell
curl -X POST -F "file=@notes.md" http://127.0.0.1:8000/upload/document
```

支持类型包括：

```text
pdf, md, txt, py, cpp, c, h, hpp, yaml, yml, json, toml
```

### 上传实验 CSV

```powershell
curl -X POST -F "file=@results.csv" http://127.0.0.1:8000/upload/csv
```

### 扫描代码项目

```powershell
curl -X POST http://127.0.0.1:8000/project/scan ^
  -H "Content-Type: application/json" ^
  -d "{\"project_path\":\"D:/Projects/example\"}"
```

### 调用 Agent 问答

```powershell
curl -X POST http://127.0.0.1:8000/chat ^
  -H "Content-Type: application/json" ^
  -d "{\"question\":\"这篇论文的核心创新是什么？\",\"source_type\":\"paper\",\"source_id\":\"1\"}"
```

`source_type` 可选：

```text
paper
project
csv
general
```

## 前端页面

Streamlit 中文界面包含：

- 总览：查看系统能力和已入库资料。
- 资料入库：上传 PDF、Markdown、txt、代码和配置文件，生成 embedding 并写入向量库。
- 论文阅读：上传 PDF 论文并建立论文索引。
- 代码项目：输入本地项目路径，扫描目录并建立代码索引。
- 实验 CSV：上传实验结果文件并自动分析指标。
- 智能问答：选择知识源类型和 source_id，运行 LangGraph Agent 工作流。
- 资料与日志：查看文档列表和会话日志。

## 后端接口

```text
POST /upload/paper      上传 PDF 论文并建立索引
POST /upload/document   上传通用资料并建立 RAG 索引
POST /upload/csv        上传实验 CSV
POST /project/scan      扫描并索引代码项目
POST /chat              调用 Agent 问答
GET  /documents         查看已上传资料
GET  /logs/{session_id} 查看会话和工具调用日志
GET  /health            健康检查
```

## 测试

推荐显式指定 pytest 临时目录，避免 Windows 默认 Temp 权限问题：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_csv_tools.py tests/test_code_tools.py tests/test_rag.py -q --basetemp .pytest_tmp
```

当前基础测试覆盖：

- CSV schema 与指标分析
- 代码目录扫描与 Python 函数/类提取
- 文本文档 RAG 入库与检索

## 后续扩展方向

- 接入真正的 MCP Server，把本地 Tool Registry 升级为标准 MCP 工具服务。
- 增加 PDF 页码级引用和章节识别能力。
- 引入 AST/parser，增强多语言代码理解。
- 增加检索质量评估、回答忠实度评估和 Agent trace 可视化。
- 接入 Zotero、GitHub、Overleaf、Google Drive 等科研数据源。
- 增加图表生成，把实验 CSV 分析结果转成论文可用图表。
- 支持多文档集合和跨论文综述。
