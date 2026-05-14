import os
import requests
import logging
import time
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Zalo AI Bridge")

# Cấu hình Logging chuyên nghiệp
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# =========================
# CONFIG
# =========================
CHATBOT_API = os.getenv("CHATBOT_API")
CHATBOT_API_KEY = os.getenv("CHATBOT_API_KEY")
ZALO_SEND_API = os.getenv("ZALO_SEND_API")
GROUP_ID = os.getenv("GROUP_ID")
BRIDGE_API_KEY = os.getenv("BRIDGE_API_KEY") # Không để default để đảm bảo an toàn

if not all([CHATBOT_API, CHATBOT_API_KEY, ZALO_SEND_API, GROUP_ID, BRIDGE_API_KEY]):
    raise ValueError("Thiếu cấu hình trong file .env! Vui lòng kiểm tra lại đầy đủ các biến.")

# =========================
# MODELS & SECURITY
# =========================
class IncomingMessage(BaseModel):
    message: str
    user_name: str = "Anonymous"
    user_id: str # Bắt buộc phải có user_id để phân tách session
    group_id: str | None = None # Linh hoạt, nếu None sẽ lấy GROUP_ID từ .env

def verify_bridge_key(x_bridge_key: str = Header(None)):
    if x_bridge_key != BRIDGE_API_KEY:
        logging.warning("Unauthorized access attempt (Invalid or missing key).")
        raise HTTPException(status_code=401, detail="Invalid Bridge API Key")
    return x_bridge_key

# =========================
# CORE LOGIC
# =========================

def ask_chatbot(message: str, user_name: str, group_id: str, user_id: str):
    # Fix 1: Thêm prefix 'zalo_' và định danh theo cặp Group + User
    session_id = f"zalo_{group_id}_{user_id}"
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": CHATBOT_API_KEY
    }

    payload = {
        "session_id": session_id,
        "message": message,
        "user_name": user_name
    }

    try:
        logging.info(f"[CHAT] {user_name} ({group_id}): {message}")
        
        # Fix 2: Tách timeout (5s connect, 60s read)
        response = requests.post(
            CHATBOT_API,
            headers=headers,
            json=payload,
            timeout=(5, 60)
        )
        response.raise_for_status()
        
        # Fix 3: Validate JSON để tránh crash nếu server trả về HTML/Error
        try:
            data = response.json()
        except Exception:
            return "Lỗi: Chatbot trả về dữ liệu không phải JSON."

        bot_reply = data.get("reply", "Bot không có phản hồi.")
        logging.info(f"[BOT] -> {user_name}: {bot_reply}")
        return bot_reply

    except requests.exceptions.Timeout:
        return "Chatbot phản hồi quá lâu (Timeout)."
    except Exception as e:
        logging.error(f"Chatbot API Error: {str(e)}")
        return f"Lỗi hệ thống Chatbot: {str(e)}"

def send_zalo_message(text: str, group_id: str):
    payload = {
        "groupId": group_id,
        "msg": text
    }

    # Fix 4: Thêm Retry cho Zalo vì mạng có thể lag
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                ZALO_SEND_API,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=(5, 20)
            )
            response.raise_for_status()
            
            # Kiểm tra response JSON an toàn
            try:
                return response.json()
            except Exception:
                return {"status": "success", "raw_response": response.text}

        except Exception as e:
            logging.warning(f"Zalo Retry {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                return {"error": f"Failed after {max_retries} attempts: {str(e)}"}
            time.sleep(1) # Nghỉ 1s trước khi thử lại

# =========================
# ENDPOINTS
# =========================

@app.post("/zalo-chat")
def zalo_chat(data: IncomingMessage, key: str = Depends(verify_bridge_key)):
    # Validate message không được rỗng
    if not data.message or not data.message.strip():
        raise HTTPException(status_code=400, detail="Message không được để trống")

    raw_text = data.message.strip()

    # 1. Chỉ trigger AI khi tin nhắn bắt đầu bằng lệnh /ai (không phân biệt hoa thường)
    if not raw_text.lower().startswith("/ai"):
        return {
            "status": "ignored",
            "reason": "Not an AI command (must start with /ai)"
        }

    # Loại bỏ prefix /ai (3 ký tự) để lấy nội dung thực tế
    clean_message = raw_text[3:].strip()
    if not clean_message:
        return {"status": "ignored", "reason": "Empty command content"}

    # 2. Xác định group_id và kiểm tra quyền hạn
    incoming_group_id = data.group_id or GROUP_ID
    
    # Chỉ trả lời nếu tin nhắn đến từ đúng Group được cấu hình trong .env
    if incoming_group_id != GROUP_ID:
        logging.info(f"Ignored message from unauthorized group: {incoming_group_id}")
        return {
            "status": "ignored",
            "reason": "Unauthorized group"
        }
    
    target_group_id = GROUP_ID

    # 3. Hỏi chatbot
    bot_reply = ask_chatbot(
        clean_message,
        data.user_name,
        target_group_id,
        data.user_id
    )
    # 4. Kiểm tra nếu có lỗi từ AI thì không gửi vào Group (Kiểm tra linh hoạt hơn)
    error_keywords = ["lỗi", "error", "timeout", "exception", "lỗi hệ thống", "failed"]
    if any(kw in bot_reply.lower() for kw in error_keywords):
        logging.error(f"Chatbot returned error, skipping Zalo send: {bot_reply}")
        return {
            "status": "chatbot_error",
            "detail": bot_reply
        }

    # 5. Gửi về zalo
    zalo_result = send_zalo_message(bot_reply, target_group_id)

    return {
        "status": "success",
        "bot_reply": bot_reply,
        "zalo_result": zalo_result
    }

@app.get("/")
def home():
    return {
        "status": "Zalo AI bridge running",
        "features": ["Personalized Session", "Retry Logic", "Secure Endpoint"]
    }