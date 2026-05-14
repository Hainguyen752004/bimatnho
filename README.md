# Zalo AI Bridge - Hệ thống tích hợp AI Chatbot vào Zalo Group

Dự án này cung cấp một giải pháp "Bridge" (Cầu nối) mạnh mẽ, cho phép tích hợp bất kỳ AI Chatbot nào vào Zalo Group thông qua tài khoản cá nhân (đóng vai trò listener) và Zalo Send API (đóng vai trò sender).

## 🛠️ Công nghệ sử dụng
- **Zalo Listener**: Sử dụng thư viện [zca-js](https://github.com/mra-9/zca-js) - Một bộ công cụ mã nguồn mở tuyệt vời để tương tác với Zalo.
- **FastAPI Bridge**: Xây dựng bằng Python để điều phối và quản lý phiên (session) người dùng.

- **Personalized Memory**: Mỗi người dùng trong group có một bộ nhớ (session) riêng biệt dựa trên `group_id` và `user_id`.
- **Hybrid Architecture**: Sự kết hợp hoàn hảo giữa **Node.js** (hiệu năng cao cho listener) và **Python/FastAPI** (linh hoạt cho xử lý logic/AI).
- **Smart Filtering**: 
    - Chỉ phản hồi khi có lệnh `/ai` (không phân biệt hoa thường).
    - Tự động lọc các thông báo lỗi kỹ thuật, không spam vào Group.
- **Robustness**: Cơ chế tự động thử lại (Retry) khi gửi tin nhắn Zalo thất bại.
- **Security**: Bảo vệ endpoint bằng `X-Bridge-Key`.
- **Safe Testing**: Khóa cứng hoạt động trong đúng Group ID được cấu hình trong `.env`.

## 🏗️ Sơ đồ hoạt động

```text
Người dùng Zalo (Group) 
      ↓
[Listener.js] (Sử dụng zca-js để lắng nghe tin nhắn)
      ↓ (POST /zalo-chat)
[Test.py] (FastAPI Bridge - Xử lý Logic & Session)
      ↓
[Chatbot API] (Bộ não AI xử lý câu hỏi)
      ↓
[Zalo Send API] (Gửi phản hồi về đúng Group)
```

## 🛠️ Hướng dẫn cài đặt

### 1. Yêu cầu hệ thống
- **Python 3.10+**
- **Node.js 18+**

### 2. Cài đặt Python (Brain)
```bash
# Tạo môi trường ảo (khuyên dùng)
conda create -n zalo python=3.10
conda activate zalo

# Cài đặt thư viện
pip install -r requirements.txt
```

### 3. Cài đặt Node.js (Listener)
```bash
npm install
```

### 4. Cấu hình môi trường (.env)
Tạo file `.env` và điền đầy đủ thông tin sau:
```env
CHATBOT_API=http://your-chatbot-api.com/chat
CHATBOT_API_KEY=your_api_key
ZALO_SEND_API=http://your-zalo-gateway.com/send-message
GROUP_ID=target_group_id
BRIDGE_API_KEY=SECRET_KEY_123
```

> [!IMPORTANT]  
> **Lưu ý về Chatbot API (Bộ não AI):** Dự án này chỉ cung cấp phần "Cầu nối" (Bridge). Bạn cần phải tự xây dựng hoặc có sẵn một Chatbot API của riêng mình (ví dụ: GPT-4, Gemini, hoặc bot tự học) để xử lý câu hỏi và trả về câu trả lời.

## 🏃 Cách vận hành

Hệ thống cần chạy song song 2 thành phần:

1. **Khởi động Não bộ (Python):**
   ```bash
   uvicorn test:app --reload
   ```

2. **Khởi động Tai nghe (Node.js):**
   ```bash
   node listener.js
   ```
   *Lưu ý: Quét mã QR hiện ra để đăng nhập vào tài khoản Zalo dùng để lắng nghe.*

## 📝 Cách sử dụng trong Zalo
Vào Group đã cấu hình, gõ lệnh theo cú pháp:
` /ai [Câu hỏi của bạn] `

Ví dụ: `/ai Chào bot, bạn có thể giúp tôi tư vấn sản phẩm không?`

---
**Author:** Chí Hải
**Repo:** [Hainguyen752004/bimatnho](https://github.com/Hainguyen752004/bimatnho)
