import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Tải biến môi trường từ file .env
load_dotenv()

class SlotFillingFlightBot:
    """
    Hệ thống Chatbot Đặt vé máy bay tự động sử dụng kỹ thuật Slot Filling.
    
    Các thông tin (Slots) cần thu thập:
    - departure_city: Điểm đi
    - destination_city: Điểm đến
    - travel_date: Ngày bay (YYYY-MM-DD hoặc định dạng ngày)
    - passenger_count: Số lượng hành khách (Số nguyên)
    - ticket_class: Hạng vé (Economy/Business/First Class)
    """

    def __init__(self, api_key: Optional[str] = None):
        # Khởi tạo OpenAI Client
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("Không tìm thấy OPENAI_API_KEY. Vui lòng thiết lập biến môi trường hoặc truyền trực tiếp.")
        
        self.client = OpenAI(api_key=key)
        self.model = "gpt-4o-mini"  # Hoặc "gpt-3.5-turbo" / "gpt-4o"

        # Khởi tạo trạng thái các slots (Mặc định là None)
        self.slots: Dict[str, Any] = {
            "departure_city": None,
            "destination_city": None,
            "travel_date": None,
            "passenger_count": None,
            "ticket_class": None
        }

    def _build_system_prompt(self) -> str:
        """
        Thiết kế System Prompt định hướng cho LLM xử lý Slot Filling.
        Yêu cầu LLM trả về kết quả dưới dạng cấu trúc JSON cố định.
        """
        return f"""
Bạn là một trợ lý thông minh hỗ trợ đặt vé máy bay. 
Nhiệm vụ của bạn là thu thập đủ 5 thông tin (slots) sau từ người dùng:
1. departure_city: Điểm đi (Thành phố/Sân bay)
2. destination_city: Điểm đến (Thành phố/Sân bay)
3. travel_date: Ngày bay
4. passenger_count: Số lượng hành khách (integer)
5. ticket_class: Hạng vé (ví dụ: Economy, Business, phổ thông, thương gia)

TRẠNG THÁI HIỆN TẠI CỦA CÁC SLOTS:
{json.dumps(self.slots, ensure_ascii=False, indent=2)}

QUY TẮC XỬ LÝ:
1. Phân tích tin nhắn mới nhất của người dùng để cập nhật hoặc giữ nguyên các thông tin trong trạng thái hiện tại.
2. Nếu người dùng muốn đổi thông tin đã có, hãy cập nhật lại giá trị mới.
3. Xác định các slot còn thiếu (giá trị vẫn là null).
4. Tạo một câu phản hồi tự nhiên, thân thiện bằng tiếng Việt:
   - Nếu vẫn còn slot thiếu: Hãy hỏi người dùng thông tin còn thiếu tiếp theo (Ưu tiên hỏi 1-2 slot còn thiếu tự nhiên nhất).
   - Nếu đã đủ tất cả 5 slots: Xác nhận lại toàn bộ thông tin đặt vé với khách hàng.

ĐẦU RA BẮT BUỘC (Định dạng JSON duy nhất, không thêm Markdown hay giải thích ngoài JSON):
{{
  "updated_slots": {{
    "departure_city": string hoặc null,
    "destination_city": string hoặc null,
    "travel_date": string hoặc null,
    "passenger_count": integer hoặc null,
    "ticket_class": string hoặc null
  }},
  "bot_response": "Câu trả lời gửi đến người dùng",
  "is_complete": true/false
}}
"""

    def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Xử lý tin nhắn của người dùng, gọi API LLM và cập nhật Slot state.
        """
        system_prompt = self._build_system_prompt()

        try:
            # Gọi OpenAI API với định dạng bắt buộc JSON Response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.2  # Giữ nhiệt độ thấp để trích xuất dữ liệu chính xác
            )

            content = response.choices[0].message.content
            parsed_data = json.loads(content)

            # Cập nhật lại State của các Slots trong Bot
            if "updated_slots" in parsed_data:
                self.slots = parsed_data["updated_slots"]

            return parsed_data

        except Exception as e:
            return {
                "updated_slots": self.slots,
                "bot_response": f"Rất tiếc, đã có lỗi xảy ra trong quá trình xử lý: {str(e)}",
                "is_complete": False
            }

    def print_slot_status(self):
        """Hiển thị bảng trạng thái Slot hiện tại trên Console"""
        print("\n" + "="*40)
        print(" TRẠNG THÁI SLOT HIỆN TẠI")
        print("="*40)
        for key, value in self.slots.items():
            status = f"✅ {value}" if value is not None else "❌ Chưa có"
            print(f" - {key:<18}: {status}")
        print("="*40 + "\n")


def main():
    """Chương trình chạy chính tương tác trên CLI"""
    print("="*60)
    print("   HỆ THỐNG TRỢ LÝ ĐẶT VÉ MÁY BAY AUTO SLOT FILLING (PTIT AI)")
    print("="*60)
    print("Gõ 'exit' hoặc 'quit' để thoát chương trình.\n")

    # Khởi tạo Bot
    try:
        bot = SlotFillingFlightBot()
    except Exception as e:
        print(f"Lỗi khởi tạo: {e}")
        print("Vui lòng thiết lập OPENAI_API_KEY trong file .env")
        return

    # Lời chào đầu tiên
    print("Bot: Xin chào! Tôi là trợ lý đặt vé máy bay. Bạn muốn đi đâu?")

    while True:
        try:
            user_input = input("\nBạn: ").strip()
            
            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit"]:
                print("\nBot: Cảm ơn bạn đã sử dụng dịch vụ. Tạm biệt!")
                break

            # Xử lý tin nhắn
            result = bot.process_message(user_input)

            # Hiển thị phản hồi từ Bot
            print(f"\nBot: {result.get('bot_response')}")

            # Hiển thị bảng kiểm tra Slots
            bot.print_slot_status()

            # Nếu đã điền đủ thông tin -> Hoàn thành tác vụ
            if result.get("is_complete", False):
                print("🎉 CHÚC MỪNG! Đã hoàn tất thu thập thông tin đặt vé.")
                print("Hệ thống tiến hành chuyển sang bước Thanh toán/Xác nhận booking...")
                break

        except KeyboardInterrupt:
            print("\nĐã hủy thao tác.")
            break

if __name__ == "__main__":
    main()