const { Zalo } = require("zca-js");
const fetch = require("node-fetch");
require('dotenv').config();

const BRIDGE_URL = "http://127.0.0.1:8000/zalo-chat";
const BRIDGE_KEY = process.env.BRIDGE_API_KEY || "SECRET_KEY_123";

const zalo = new Zalo();

async function startBot() {
    try {
        console.log("------------------------------------------");
        console.log("🚀 ĐANG KHỞI ĐỘNG TAI NGHE ZALO...");
        console.log("------------------------------------------");

        // 1. Đăng nhập
        const api = await zalo.loginQR();
        console.log("\n✅ ĐĂNG NHẬP THÀNH CÔNG!");
        
        // Debug: Xem trong api có những gì
        console.log("API Keys:", Object.keys(api));

        // 2. Lấy listener từ api
        const { listener } = api;

        // 3. Đăng ký sự kiện lắng nghe tin nhắn
        listener.on("message", async (msg) => {
            // Chỉ xử lý tin nhắn văn bản trong Group và không phải tin nhắn của chính mình
            if (msg.type === "text" && msg.isGroup && !msg.isSelf) {
                
                console.log(`\n[📩 Nhận tin] ${msg.senderName}: ${msg.message}`);

                try {
                    const response = await fetch(BRIDGE_URL, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-Bridge-Key": BRIDGE_KEY
                        },
                        body: JSON.stringify({
                            message: msg.message,
                            user_name: msg.senderName,
                            user_id: msg.senderId,
                            group_id: msg.threadId
                        })
                    });

                    const data = await response.json();
                    
                    if (data.status === "success") {
                        console.log(`[🤖 Bot Rep]: ${data.bot_reply}`);
                    } else if (data.status === "ignored") {
                        console.log(`[ℹ️ Bỏ qua]: ${data.reason}`);
                    } else {
                        console.error("[❌ Lỗi Bridge]:", data);
                    }

                } catch (error) {
                    console.error("[‼️ Lỗi kết nối]: Hãy đảm bảo test.py (uvicorn) đang chạy!");
                }
            }
        });

        // 4. QUAN TRỌNG: Phải gọi start() thì nó mới bắt đầu nghe
        listener.start();
        console.log("📡 ĐANG LẮNG NGHE TIN NHẮN TỰ ĐỘNG...");

    } catch (error) {
        console.error("❌ Lỗi khởi động bot:", error.message);
    }
}

startBot();
