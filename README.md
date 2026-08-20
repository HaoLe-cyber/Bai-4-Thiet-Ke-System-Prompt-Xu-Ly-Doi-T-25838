# Bài 4: Thiết Kế System Prompt & Xử Lý Đối Thoại Điền Khuyết Thông Tin (Slot Filling)

**Môn học:** AI Integration (PTIT - K24)  
**Chủ đề:** Prompt Engineering & Stateful Dialogue Management with LLMs.

---

## 📝 Mô tả Bài tập

Trong các hệ thống hỗ trợ đối thoại giao dịch (Task-oriented Dialogue Systems) như đặt vé, đặt bàn, tư vấn bán hàng,... LLM cần phải thu thập đủ các trường thông tin quan trọng (**Slots**) trước khi thực hiện hành động (Action/API call).

Bài tập này triển khai một **Hệ thống Đặt Vé Máy Bay Tự Động (Slot-Filling Assistant)** có khả năng:
1. **Thiết kế System Prompt nâng cao:** Buộc mô hình phản hồi theo dạng JSON chuẩn hóa để ứng dụng dễ dàng bóc tách dữ liệu.
2. **Quản lý trạng thái (State Tracking):** Lưu giữ các thông tin đã thu thập (`departure_city`, `destination_city`, `travel_date`, `passenger_count`, `ticket_class`).
3. **Phát hiện slot thiếu (Slot Verification):** Nhận biết thông tin nào chưa có để sinh câu hỏi gợi mở tiếp theo cho người dùng.
4. **Xác nhận giao dịch:** Tự động phát hiện khi toàn bộ slots đã được lấp đầy để chuyển sang luồng thanh toán/xác nhận.

---

## 🛠️ Yêu cầu môi trường & Cài đặt

### 1. Cài đặt Python
Yêu cầu Python version >= 3.9

### 2. Cài đặt thư viện phụ thuộc
Tạo môi trường ảo (khuyên dùng) và cài đặt các thư viện cần thiết:

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Cài đặt gói phụ thuộc
pip install openai python-dotenv
```

### 3. Cấu hình API Key
Tạo file `.env` nằm cùng thư mục gốc với file `main.py` và thêm khoá OpenAI API của bạn:

```env
OPENAI_API_KEY=sk-proj-xxxxxxYOUR_ACTUAL_API_KEYxxxxxx
```

---

## 🚀 Cách chạy chương trình

Chạy trực tiếp file `main.py` bằng Python:

```bash
python main.py
```

---

## 💬 Kịch bản demo kiểm thử (Test Scenario)

### Kịch bản 1: Cung cấp thông tin rải rác qua nhiều lượt thoại

* **Lượt 1 (Mới đưa điểm đi/đến):**
  * **Bạn:** *Tôi muốn bay từ Hà Nội vào Sài Gòn.*
  * **Bot:** *Chào bạn, tôi đã ghi nhận chuyến bay từ Hà Nội đến Sài Gòn. Bạn dự định bay vào ngày nào?*
  * **Slot Tracking:** `departure_city` & `destination_city` được điền.

* **Lượt 2 (Đưa ngày bay và hạng vé):**
  * **Bạn:** *Ngày 25 tháng 12 này nhé, tôi đi vé thương gia.*
  * **Bot:** *Dự định chuyến bay ngày 25/12/2024 hạng Thương gia (Business). Bạn đi một mình hay có mấy người?*
  * **Slot Tracking:** `travel_date` & `ticket_class` được điền.

* **Lượt 3 (Đưa số lượng người):**
  * **Bạn:** *Mình đi 2 người nhé.*
  * **Bot:** *Cảm ơn bạn! Tôi đã ghi nhận thông tin đặt vé: Khởi hành từ Hà Nội đến Sài Gòn vào ngày 25/12/2024 cho 2 hành khách hạng Thương gia. Bạn xác nhận đặt vé chứ?*
  * **Slot Tracking:** Đủ 5/5 Slots -> `is_complete: true`.

---

## 🧠 Giải thích kiến trúc & Code

1. **JSON Output Schema Enforcement (`response_format={"type": "json_object"}`):**
   - Buộc LLM tuân thủ chính xác cấu trúc dữ liệu JSON đầu ra. Giúp phần mã Python đọc và cập nhật dictionary `self.slots` một cách an toàn mà không cần Regex phức tạp.

2. **System Prompt Injection:**
   - Trong mỗi lượt hội thoại, hàm `_build_system_prompt()` sẽ tiêm (inject) trạng thái `self.slots` hiện tại vào prompt. Nhờ đó, LLM luôn ý thức được thông tin nào **đã có** và thông tin nào **còn thiếu**.

3. **Tách biệt Logic (Decoupling Logic & LLM):**
   - LLM đảm nhận việc NLU (Natural Language Understanding) và sinh lời thoại tự nhiên.
   - Code Python quản lý trạng thái biến (`self.slots`) và quyết định luồng ứng dụng (`is_complete`).