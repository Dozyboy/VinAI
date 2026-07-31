from src.config import get_settings
s = get_settings()
print(f"provider={s.llm_provider}")
print(f"openai_key={'SET' if s.openai_api_key else 'EMPTY'}")
print(f"model={s.model_name}")

from langchain_openai import ChatOpenAI
try:
    llm = ChatOpenAI(model=s.model_name, api_key=s.openai_api_key)
    print("ChatOpenAI created OK")
except Exception as e:
    print(f"ChatOpenAI creation failed: {type(e).__name__}: {e}")
