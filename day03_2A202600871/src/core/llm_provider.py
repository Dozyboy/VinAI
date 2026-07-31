import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Generator
from pathlib import Path
from dotenv import load_dotenv

# Tự động tìm đường dẫn file .env nằm ở thư mục src/core/.env
DEFAULT_ENV_PATH = Path(__file__).resolve().parent / ".env"

class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    Supports OpenAI, Gemini, and Local models.
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        pass

# =====================================================================
# HÀM FACTORY KHỞI TẠO ĐỘNG (THÊM VÀO ĐỂ CHẠY CHO CHATBOT.PY)
# =====================================================================
def get_llm_provider(env_path: Path = DEFAULT_ENV_PATH) -> LLMProvider:
    """
    Đọc cấu hình file .env và trả về đối tượng Provider tương ứng.
    """
    if not env_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file cấu hình .env tại {env_path}")
        
    load_dotenv(dotenv_path=env_path)
    
    provider_type = os.getenv("DEFAULT_PROVIDER", "openai").lower().strip()
    
    if provider_type == "local":
        from src.core.local_provider import LocalProvider
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf").strip()
        print(f"--- [HỆ THỐNG] Đang tải mô hình CPU Local: {os.path.basename(model_path)} ---")
        return LocalProvider(model_path=model_path)
        
    elif provider_type == "gemini":
        from src.core.gemini_provider import GeminiProvider
        model_name = os.getenv("MODEL", "gemini-1.5-flash").strip()
        api_key = os.getenv("API_KEY")
        return GeminiProvider(model_name=model_name, api_key=api_key)
        
    else: # Mặc định là openai hoặc openrouter sử dụng chung định dạng
        from src.core.openai_provider import OpenAIProvider
        model_name = os.getenv("MODEL", "gpt-4o").strip()
        api_key = os.getenv("API_KEY")
        
        # Tạo instance cho OpenAIProvider
        provider = OpenAIProvider(model_name=model_name, api_key=api_key)
        
        # Nếu dùng cổng OpenRouter, ta bổ sung thêm base_url và headers đặc thù
        llm_endpoint = os.getenv("LLM_ENDPOINT", "").strip()
        if "openrouter.ai" in llm_endpoint:
            provider.client.base_url = llm_endpoint
            provider.client.default_headers = {
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "AI Lab Agent"
            }
        return provider