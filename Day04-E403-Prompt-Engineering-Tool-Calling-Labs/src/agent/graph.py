from __future__ import annotations

import json
from pathlib import Path

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from src.core.llm import build_chat_model, normalize_content
from src.core.schemas import (
    AgentResult,
    CalculateTotalsInput,
    DiscountInput,
    ListProductsInput,
    ProductDetailInput,
    SaveOrderInput,
    ToolCallRecord,
)
from src.utils.data_store import OrderDataStore

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT_DIR / "data"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "artifacts" / "orders"

def build_system_prompt(today: str | None = None) -> str:
    current_day = today or "2026-06-01"
    return f"""You are an elite AI Order Assistant for an electronics retailer. Today is {current_day}.
Your sole purpose is to process user orders by STRICTLY following the rules below.

CRITICAL RULES (FAILING THESE WILL CAUSE SYSTEM CRASH):

1. LANGUAGE: ALWAYS respond to the user in Vietnamese.

2. GUARDRAILS FIRST: IMMEDIATELY REFUSE the request (in Vietnamese) WITHOUT calling any tools if the user asks to:
   - Bypass or ignore stock/inventory limitations.
   - Create fake invoices.
   - Apply manual, fake, or unauthorized discounts.
   
3. CLARIFICATION SECOND: Before starting the order process, you MUST verify if the user provided ALL of the following:
   - Customer Name
   - Phone Number
   - Email
   - Shipping Address
   - Exact Product Name(s) and Quantity
   If ANY of this is missing, DO NOT call any tools. Stop and ask the user for the missing details in Vietnamese.

4. THE UNBREAKABLE 5-STEP WORKFLOW:
   If the request is safe and ALL customer information is provided, you MUST execute the following 5 tools in this EXACT sequential order. 
   DO NOT stop or ask the user for confirmation between steps. CHAIN THEM TOGETHER:
   - Step 1: `list_products` -> Find the exact `product_id`.
   - Step 2: `get_product_details` -> Pass the `product_ids` from Step 1. Extract the `detail_token`.
   - Step 3: `get_discount` -> Pass the customer's email as `seed_hint`. Extract the `discount_rate` and `campaign_code`.
   - Step 4: `calculate_order_totals` -> Pass the items, `detail_token` (from Step 2), and `discount_rate` (from Step 3).
   - Step 5: `save_order` -> Pass all customer info, items, `detail_token`, `discount_rate`, and `campaign_code`.

5. GROUNDING: NEVER hallucinate prices, discounts, file paths, or order IDs. 

6. FINAL CONFIRMATION: ONLY after `save_order` is successfully executed, output a concise confirmation to the user in Vietnamese containing the Order ID and the Final Total amount.
""".strip()

def build_tools(store: OrderDataStore):
    @tool(args_schema=ListProductsInput)
    def list_products(query: str = "", category: str = "", max_unit_price: int = None, required_tags: list = [], in_stock_only: bool = True, limit: int = 8) -> str:
        """Step 1: Search for products in the catalog based on user request. 
        ALWAYS call this first to get the exact product_id.
        Do not call this multiple times if you already found the product.
        """
        return json.dumps(store.list_products(query=query, category=category, max_unit_price=max_unit_price, required_tags=required_tags, in_stock_only=in_stock_only, limit=limit), ensure_ascii=False)

    @tool(args_schema=ProductDetailInput)
    def get_product_details(product_ids: list[str]) -> str:
        """Step 2: Get pricing details and generate a secure detail_token.
        You MUST pass the exact product_ids found from list_products.
        You MUST extract the detail_token from the output of this tool to use in Step 4 and 5.
        """
        return json.dumps(store.get_product_details(product_ids=product_ids), ensure_ascii=False)

    @tool(args_schema=DiscountInput)
    def get_discount(seed_hint: str, customer_tier: str = "standard") -> str:
        """Step 3: Get the valid discount_rate and campaign_code for the order.
        Use customer_email as the seed_hint.
        You MUST extract the discount_rate from the output of this tool to use in Step 4 and 5.
        """
        return json.dumps(store.get_discount(seed_hint=seed_hint, customer_tier=customer_tier), ensure_ascii=False)

    @tool(args_schema=CalculateTotalsInput)
    def calculate_order_totals(items: list, detail_token: str, discount_rate: float) -> str:
        """Step 4: Calculate the final total amount.
        You MUST provide the items list, the detail_token from Step 2, and the discount_rate from Step 3.
        """
        return json.dumps(store.calculate_order_totals(items=items, detail_token=detail_token, discount_rate=discount_rate), ensure_ascii=False)

    @tool(args_schema=SaveOrderInput)
    def save_order(customer_name: str, customer_phone: str, customer_email: str, shipping_address: str, items: list, detail_token: str, discount_rate: float, campaign_code: str, customer_tier: str = "standard", notes: str = "") -> str:
        """Step 5: Save the order to the database.
        Call this ONLY AFTER calculate_order_totals is successful.
        Requires all customer info, items, detail_token (from Step 2), discount_rate (from Step 3), and campaign_code (from Step 3).
        """
        return json.dumps(store.save_order(customer_name=customer_name, customer_phone=customer_phone, customer_email=customer_email, shipping_address=shipping_address, items=items, detail_token=detail_token, discount_rate=discount_rate, campaign_code=campaign_code, customer_tier=customer_tier, notes=notes), ensure_ascii=False)

    return [list_products, get_product_details, get_discount, calculate_order_totals, save_order]

def build_agent(provider: str = "google", model_name: str | None = None, today: str | None = None):
    store = OrderDataStore(DEFAULT_DATA_DIR, DEFAULT_OUTPUT_DIR, today=today)
    llm = build_chat_model(provider=provider, model_name=model_name)
    tools = build_tools(store)
    system_prompt = build_system_prompt(today)
    
    # Tạo React Agent của LangChain
    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)


def run_agent(
    query: str,
    *,
    provider: str = "google",
    model_name: str | None = None,
    data_dir: Path | None = None,
    output_dir: Path | None = None,
    today: str | None = None,
) -> AgentResult:
    # 1. Khởi tạo Agent
    agent = build_agent(provider=provider, model_name=model_name, today=today)
    
    # 2. Chạy Agent với câu hỏi của người dùng
    response = agent.invoke({"messages": [{"role": "user", "content": query}]})
    messages = response.get("messages", [])
    
    # 3. Trích xuất thông tin
    final_answer = extract_final_answer(messages)
    tool_calls = extract_tool_calls(messages)
    saved_order_payload, saved_order_path = extract_saved_order(tool_calls)
    
    # 4. Trả về kết quả cho bộ chấm điểm
    return AgentResult(
        query=query,
        final_answer=final_answer,
        tool_calls=tool_calls,
        saved_order_payload=saved_order_payload,
        saved_order_path=saved_order_path,
        provider=provider,
        model_name=model_name or "default"
    )


def extract_final_answer(messages) -> str:
    """Helper: Lấy câu trả lời cuối cùng của AI từ danh sách tin nhắn."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return ""


def extract_tool_calls(messages) -> list[ToolCallRecord]:
    """Helper: Lọc ra danh sách các công cụ mà AI đã gọi cùng với kết quả (output) của chúng."""
    records = []
    for msg in messages:
        # Nếu là tin nhắn của AI và có gọi tool
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                # Tìm ToolMessage tương ứng trong lịch sử để lấy kết quả (output)
                tool_output = ""
                for tool_msg in messages:
                    if isinstance(tool_msg, ToolMessage) and tool_msg.tool_call_id == tc["id"]:
                        tool_output = tool_msg.content
                        break
                
                records.append(ToolCallRecord(
                    name=tc["name"], 
                    args=tc.get("args", {}),
                    output=tool_output
                ))
    return records


def extract_saved_order(tool_calls: list[ToolCallRecord]) -> tuple[dict | None, str | None]:
    """Helper: Trích xuất payload và đường dẫn file từ kết quả của tool save_order."""
    import json
    for tc in tool_calls:
        if tc.name == "save_order":
            if tc.output:
                try:
                    data = json.loads(tc.output)
                    saved_order = data.get("saved_order")
                    if saved_order:
                        return saved_order, saved_order.get("save_path")
                except Exception:
                    pass
    return None, None
