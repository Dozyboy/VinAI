import os
import re
from typing import List, Dict, Any, Optional
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger

class ReActAgent:
    """
    Một Agent theo mô hình ReAct (Thought-Action-Observation) hoàn chỉnh.
    """
    
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps

    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join([f"- {t['name']}: {t['description']}. Định dạng gọi: {t['name']}(đối_số)" for t in self.tools])
        return f"""Bạn là một Trợ lý Du lịch thông minh sử dụng vòng lặp ReAct (Thought-Action-Observation).
Bạn có quyền truy cập vào các công cụ sau:
{tool_descriptions}

Khi nhận được yêu cầu, bạn PHẢI tuân thủ nghiêm ngặt định dạng sau trong từng bước suy nghĩ:

Thought: Bạn đang nghĩ gì, cần làm gì tiếp theo hoặc cần thông tin gì.
Action: tên_tool(đối_số_dạng_chuỗi)
Observation: Kết quả trả về từ công cụ (Phần này hệ thống sẽ tự điền, bạn không tự chế ra).

Bạn có thể lặp lại cặp Thought/Action/Observation nhiều lần cho đến khi có đủ thông tin.
Khi đã có đủ thông tin để trả lời người dùng, bạn PHẢI kết thúc bằng định dạng:
Final Answer: Câu trả lời cuối cùng và chi tiết cho người dùng.

LƯU Ý QUAN TRỌNG: 
1. Mỗi lượt phản hồi bạn chỉ được đưa ra MỘT cặp Thought và Action. Chờ Observation rồi mới nghĩ tiếp.
2. Viết đúng tên công cụ và truyền đối số ngắn gọn rõ ràng.
"""

    def run(self, user_input: str) -> str:
        """
        Hàm thực thi vòng lặp ReAct: Thought -> Action -> Observation
        """
        logger.log_event("AGENT_START", {"input": user_input, "model": self.llm.model_name})
        
        # ĐỊNH NGHĨA BIẾN current_prompt Ở ĐÂY để lưu ngữ cảnh hội thoại
        current_prompt = f"Yêu cầu từ người dùng: {user_input}\n"
        steps = 0

        while steps < self.max_steps:
            # Gọi LLM sinh bước tiếp theo (Lấy trường ['content'] vì kết quả là Dict)
            response_dict = self.llm.generate(prompt=current_prompt, system_prompt=self.get_system_prompt())
            response = response_dict["content"]
            
            print(f"\n[Agent Step {steps+1}]:\n{response}") # In ra để theo dõi tiến trình tư duy
            
            # Lưu tư duy của Agent vào ngữ cảnh
            current_prompt += f"\n{response}"

            # Nếu tìm thấy câu trả lời cuối cùng -> Thoát vòng lặp
            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[-1].strip()
                logger.log_event("AGENT_END", {"steps": steps + 1, "status": "success"})
                return final_answer

            # Bóc tách Action bằng Regex để gọi Tool
            import re
            action_match = re.search(r"Action:\s*(\w+)\((.*)\)", response)
            if action_match:
                tool_name = action_match.group(1)
                tool_args = action_match.group(2).strip("'\" ")
                
                # Thực thi công cụ
                observation = self._execute_tool(tool_name, tool_args)
                print(f"[Observation]: {observation}")
                
                # Đưa kết quả công cụ vào ngữ cảnh để lượt sau Agent đọc
                current_prompt += f"\nObservation: {observation}"
            else:
                # Nếu model local sinh định dạng lỗi, nhắc nhở nó đi đúng hướng
                current_prompt += "\nObservation: Định dạng không hợp lệ. Hãy đưa ra 'Action: tên_tool(tham_số)' hoặc 'Final Answer: kết_quả'."
            
            steps += 1
            
        logger.log_event("AGENT_END", {"steps": steps, "status": "max_steps_reached"})
        return "Xin lỗi, tôi chưa thể hoàn thành tác vụ trong số bước quy định."
    
    def _execute_tool(self, tool_name: str, args: str) -> str:
        """Tìm và thực thi công cụ tương ứng."""
        for tool in self.tools:
            if tool['name'] == tool_name:
                try:
                    return tool['func'](args)
                except Exception as e:
                    return f"Lỗi khi thực thi công cụ {tool_name}: {str(e)}"
        return f"Công cụ '{tool_name}' không tồn tại."