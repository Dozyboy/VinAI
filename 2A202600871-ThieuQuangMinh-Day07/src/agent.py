from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Bước 1: Tìm kiếm các chunk liên quan từ Store
        results = self.store.search(question, top_k=top_k)
        
        # Bước 2: Rút trích văn bản và xây dựng Context
        contexts = [res.get("text", "") for res in results if res.get("text")]
        context_str = "\n---\n".join(contexts)
        
        # Xây dựng Prompt
        prompt = f"""Bạn là một trợ lý ảo thông minh. Hãy trả lời câu hỏi của người dùng dựa trên thông tin được cung cấp trong phần Context dưới đây.
Nếu Context không chứa thông tin để trả lời, hãy nói rằng bạn không biết, đừng tự bịa ra thông tin.

Context:
{context_str}

Question: {question}
Answer:"""

        # Bước 3: Gửi prompt cho LLM và trả về câu trả lời
        return self.llm_fn(prompt)