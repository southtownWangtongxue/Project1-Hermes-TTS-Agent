"""
RAG 模块 —— 检索增强生成（Retrieval-Augmented Generation）

提供文档切片、向量化、Milvus 向量检索与知识库管理功能。
将外部知识库文档转为向量存入 Milvus，并在需要时检索最相关的文档片段，
作为 LLM 生成的上下文依据。
"""
from app.rag.embeddings import chunk_text, embed_texts, embed_and_store
from app.rag.retriever import search_similar, get_collection_info
from app.rag.knowledge import upload_document, list_documents

__all__ = [
    # embeddings —— 文档切片与向量化
    "chunk_text",
    "embed_texts",
    "embed_and_store",
    # retriever —— Milvus 向量检索
    "search_similar",
    "get_collection_info",
    # knowledge —— 知识库管理
    "upload_document",
    "list_documents",
]
