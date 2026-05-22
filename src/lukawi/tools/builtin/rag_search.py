"""RAG tools: semantic search, file upload, document listing."""

from __future__ import annotations

from pathlib import Path

from lukawi.tools.base import (
    ToolDefinition,
    ToolResult,
    ToolParameter,
    ToolParameterType,
)
from lukawi.tools.registry import ToolRegistry


RAG_SEARCH_TOOL = ToolDefinition(
    name="rag_search",
    description=(
        "语义搜索本地知识库。可以搜索之前上传的文档内容（txt/markdown）"
        "以及历史对话记录。用于：查找文档中的信息、回忆之前的对话内容。"
    ),
    parameters=[
        ToolParameter(
            name="query",
            type=ToolParameterType.STRING,
            description="自然语言搜索查询，描述你想找什么内容",
        ),
        ToolParameter(
            name="source",
            type=ToolParameterType.STRING,
            description="搜索来源：'docs' 只搜文档, 'conversations' 只搜对话, 'all' 全部",
            required=False,
            default="all",
        ),
        ToolParameter(
            name="limit",
            type=ToolParameterType.INTEGER,
            description="最多返回多少条结果",
            required=False,
            default=5,
        ),
    ],
    category="rag",
    tags=["rag", "search", "knowledge", "documents", "memory"],
)

RAG_UPLOAD_TOOL = ToolDefinition(
    name="rag_upload",
    description=(
        "上传本地文件到知识库。上传后文件内容会被自动分块、向量化，"
        "之后可以通过 rag_search 检索。支持 .txt 和 .md 文件。"
    ),
    parameters=[
        ToolParameter(
            name="path",
            type=ToolParameterType.STRING,
            description="要上传的文件路径（支持 .txt 或 .md 文件）",
        ),
    ],
    category="rag",
    tags=["rag", "upload", "knowledge", "documents"],
)

RAG_LIST_TOOL = ToolDefinition(
    name="rag_list",
    description="列出知识库中所有已上传的文档及其基本信息。",
    parameters=[],
    category="rag",
    tags=["rag", "list", "documents", "knowledge"],
)


def register_rag_tools(
    registry: ToolRegistry,
    rag_manager=None,
) -> None:
    """Register RAG tools in the tool registry."""

    async def rag_search_handler(
        query: str, source: str = "all", limit: int = 5
    ) -> ToolResult:
        if rag_manager is None:
            return ToolResult.error("RAG 系统未启用，请在配置中开启 rag.enabled")
        try:
            sources_map = {"all": None, "docs": ["docs"], "conversations": ["conversations"]}
            sources = sources_map.get(source)
            if sources is None:
                return ToolResult.error(f"无效的 source 参数: '{source}'")
            results = await rag_manager.search(query=query, sources=sources, limit=limit)
            if not results:
                return ToolResult.success(result="未找到相关内容。", metadata={"count": 0})
            formatted = [
                {
                    "content": r.content,
                    "score": round(r.score, 4),
                    "source": r.metadata.get("source_path", "conversation"),
                    "type": r.metadata.get("type", "document"),
                }
                for r in results
            ]
            return ToolResult.success(result=formatted, metadata={"count": len(formatted)})
        except Exception as e:
            return ToolResult.error(f"RAG 检索失败: {e}")

    async def rag_upload_handler(path: str) -> ToolResult:
        if rag_manager is None:
            return ToolResult.error("RAG 系统未启用")
        try:
            file_path = Path(path).resolve()
            result = await rag_manager.upload_document(file_path)
            replaced_msg = "（已覆盖旧版本）" if result["replaced"] else ""
            return ToolResult.success(
                result=f"上传成功{replaced_msg}：{result['filename']}，共 {result['chunks']} 个文本块已索引。",
                metadata=result,
            )
        except Exception as e:
            return ToolResult.error(f"文件上传失败: {e}")

    async def rag_list_handler() -> ToolResult:
        if rag_manager is None:
            return ToolResult.error("RAG 系统未启用")
        try:
            docs = await rag_manager.list_documents()
            if not docs:
                return ToolResult.success(
                    result="知识库为空，还没有上传任何文档。使用 rag_upload 工具上传文件。"
                )
            return ToolResult.success(result=docs, metadata={"total": len(docs)})
        except Exception as e:
            return ToolResult.error(f"获取文档列表失败: {e}")

    registry.register(RAG_SEARCH_TOOL, rag_search_handler)
    registry.register(RAG_UPLOAD_TOOL, rag_upload_handler)
    registry.register(RAG_LIST_TOOL, rag_list_handler)
