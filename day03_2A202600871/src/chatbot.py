# --- Đoạn thêm đường dẫn bảo hiểm ở đầu file chatbot.py giữ nguyên ---
import os
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# --- SỬA LẠI ĐOẠN CHỖ IMPORT NÀY ---
from src.core.llm_provider import get_llm_provider  # Import hàm factory vừa tạo
from src.agent.agent import ReActAgent
from tools.travel_tools import search_flight_ticket, search_train_ticket

# Đóng gói danh sách công cụ
travel_tools = [
    {"name": "search_flight_ticket", "description": "Tra cứu giá vé máy bay. Đối số: 'Tên_tỉnh đi Tên_tỉnh'", "func": search_flight_ticket},
    {"name": "search_train_ticket", "description": "Tra cứu lịch trình và giá vé tàu hỏa. Đối số: 'Tên_tỉnh đi Tên_tỉnh'", "func": search_train_ticket}
]

def main():
    print("Đang khởi tạo cấu hình hệ thống...")
    try:
        # Tự động chọn mô hình dựa trên cấu hình file .env
        llm = get_llm_provider()
    except Exception as e:
        print(f"Lỗi khởi tạo: {e}")
        return

    agent = ReActAgent(llm=llm, tools=travel_tools, max_steps=5)

    print("\n" + "="*60)
    print("      DEMO: CHATBOT THÔNG THƯỜNG VS REACT AGENT (LOCAL RUN)")
    print("="*60)

    while True:
        user_input = input("\nBạn hỏi (gõ 'exit' để thoát): ")
        if user_input.lower() in ['exit', 'quit']:
            break
        if not user_input.strip():
            continue

        # ----------------------------------------------------
        # PHẦN 1: CHATBOT THÔNG THƯỜNG
        # ----------------------------------------------------
        print("\n" + "-"*25 + " [1. CHATBOT THÔNG THƯỜNG] " + "-"*25)
        chatbot_prompt = f"Bạn là chatbot thông thường. Hãy trả lời ngắn gọn yêu cầu: {user_input}"
        
        # Vì llm.generate trả về Dict nên ta lấy trường ['content']
        response_dict = llm.generate(prompt=chatbot_prompt)
        print(f"Chatbot trả lời:\n{response_dict['content']}")

        # ----------------------------------------------------
        # PHẦN 2: REACT AGENT
        # ----------------------------------------------------
        print("\n" + "-"*28 + " [2. REACT AGENT] " + "-"*28)
        agent_res = agent.run(user_input)
        print(f"\n=> KẾT QUẢ CUỐI CÙNG CỦA AGENT:\n{agent_res}")
        print("="*70)

if __name__ == "__main__":
    main()