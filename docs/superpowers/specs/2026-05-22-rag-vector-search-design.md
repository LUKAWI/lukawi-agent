# RAG + 向量检索功能设计规范

> 为 Lukawi Agent 添加基于 DashScope Embedding + ChromaDB 的 RAG 能力，
> 支持本地上传文件检索和对话记录语义搜索，替代现有 SQLite longterm 记忆。

**日期**: 2026-05-22
**状态**: 已确认
**方案**: B — 深度集成（RAG 作为记忆核心）

---

## 1. 概述

### 1.1 目标

- 用户可上传本地 txt/md 文件 → 自动分块、向量化、索引 → 通过语义搜索检索
- 对话历史自动向量化索引 → 替代现有 SQLite longterm 记忆的 LIKE 搜索
- Agent 通过内置工具 `rag_search` 自主决定何时检索

### 1.2 技术栈

| 组件 | 选型 | 版本 |
|------|------|------|
| Embedding 模型 | DashScope text-embedding-v3 | 1024 dims |
| 向量数据库 | ChromaDB | ≥0.5.0 |
| 文档加载 | 自研 DocumentLoader（txt/md） | — |
| 分块策略 | 句子边界切分 + 滑动窗口重叠 | chunk=500, overlap=50 |

---

## 2. 架构

### 2.1 模块结构

```
src/lukawi/rag/                    # 🆕 RAG 模块
├── __init__.py
├── embedder.py                    # DashScope Embedding 客户端
├── exceptions.py                  # 异常层次
├── document.py                    # 文档加载器 + 编码适配
├── store.py                       # ChromaDB 封装
├── retriever.py                   # 统一检索接口
└── manager.py                     # 生命周期管理
```

### 2.2 改动范围

| 文件 | 改动 | 风险 |
|------|------|------|
| `memory/manager.py` | ~20 行 — 注入 RAGManager，替代 LongTermMemory | 中 |
| `memory/longterm.py` | 0 行 — 保留但降级为可选（加 deprecated 注释） | 无 |
| `tools/builtin/rag_search.py` | 🆕 ~160 行 — 3 个工具（search/upload/list） | 无 |
| `config/models.py` | +25 行 — RAGConfig / DashScopeConfig 模型 | 低 |
| `cli/__init__.py` | +15 行 — 启动时初始化 RAG | 低 |
| `agent/core.py` | +3 行 — 每轮对话结束自动索引 | 低 |
| `data/default.yaml` | +15 行 — 配置示例 | 无 |
| `pyproject.toml` | +3 行 — chromadb, dashscope 依赖 | 低 |

---

## 3. 组件接口

### 3.1 DashScopeEmbedder

```python
class DashScopeEmbedder:
    def __init__(self, api_key: str, model="text-embedding-v3", dimensions=1024)
    async def embed(self, texts: str | list[str]) -> list[EmbeddingResult]
    async def embed_single(self, text: str) -> EmbeddingResult
```

- 批量上限 25 条/次，自动分批
- 指数退避重试（3 次），处理 429/401/超时

### 3.2 DocumentLoader

```python
class DocumentLoader:
    def __init__(self, chunk_size=500, chunk_overlap=50)
    def load_file(self, path: Path) -> list[DocumentChunk]
    def load_directory(self, path: Path) -> list[DocumentChunk]
```

- 编码回退链：UTF-8 → GBK → GB2312 → latin-1
- 按句子边界切分（段落级，非固定字符）
- 仅支持 .txt / .md / .markdown（MVP）

### 3.3 VectorStore

```python
class VectorStore:
    def __init__(self, persist_dir="./chroma_db")
    async def add_documents(self, chunks: list[DocumentChunk]) -> list[str]
    async def search_documents(self, query: str, limit=5) -> list[SearchResult]
    async def delete_document(self, source_path: str) -> int
    async def add_conversation(self, content: str, metadata: dict) -> str
    async def search_conversations(self, query: str, user_id="default", limit=5) -> list[SearchResult]
```

- 两个 Collection：`docs` + `conversations`，物理隔离
- ChromaDB 负责 embedding 调用（传入 DashScope embedding function）

### 3.4 RAGManager

```python
class RAGManager:
    async def upload_document(self, path: Path) -> dict       # 上传 + 去重
    async def search(self, query: str, **kwargs) -> list[SearchResult]
    async def index_conversation(self, content, user_id, metadata) -> str
    async def list_documents(self) -> list[dict]               # 列出已上传文件
    async def remove_document(self, source_path: str) -> int
```

### 3.5 三个工具

| 工具 | 功能 |
|------|------|
| `rag_search` | 语义搜索文档 + 对话记忆（source 参数区分） |
| `rag_upload` | 上传本地文件（自动去重、编码检测） |
| `rag_list` | 列出已上传文档 |

---

## 4. 数据流

```
上传:  rag_upload(path) → 安全校验 → 去重检查 → 编码检测 →
      分块(500 token) → 批量 embedding → ChromaDB(docs)

检索:  Agent 调用 rag_search(query) → DashScope embed(query) →
      ChromaDB.search(docs + conversations) → 合并排序 top-K →
      注入 Agent context → Agent 基于检索结果回答

索引:  每轮对话结束 → RAGManager.index_conversation(摘要) →
      DashScope embed(摘要) → ChromaDB(conversations)
```

---

## 5. 错误处理

| 错误场景 | 处理 |
|---------|------|
| embedding API 限流 | 指数退避重试 3 次 |
| embedding API 认证失败 | 抛 `EmbeddingError`，工具返回友好提示 |
| 文件不存在 | 抛 `DocumentLoadError`，工具返回错误 |
| 文件 > 10MB | 拒绝上传 |
| 不支持的格式 | 拒绝（仅 .txt/.md） |
| 非 UTF-8 编码 | GBK/GB2312 回退解码 |
| ChromaDB 目录权限 | 启动时检测并报错 |
| 对话索引失败 | log warning，不中断对话 |

---

## 6. 配置

```yaml
rag:
  enabled: true
  dashscope:
    api_key: ${DASHSCOPE_API_KEY}
    model: text-embedding-v3
    dimensions: 1024
  chroma_db_dir: ~/.lukawi/chroma_db
  chunk_size: 500
  chunk_overlap: 50
  max_retrieval: 10
```

---

## 7. 测试覆盖

| 测试文件 | 测试数 | 重点 |
|---------|--------|------|
| `test_embedder.py` | ~12 | mock API、批量、重试、错误码 |
| `test_document.py` | ~15 | 加载/分块/编码回退/空文件 |
| `test_store.py` | ~12 | 增删查、多 Collection、持久化 |
| `test_retriever.py` | ~8 | 混合检索、来源过滤、排序 |
| `test_manager.py` | ~10 | 生命周期、完整上传链路 |
| `test_rag_search.py` | ~8 | 工具 handler、路径安全 |
