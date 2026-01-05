import streamlit as st
import requests
import time
import json

# --- 1. CẤU HÌNH KẾT NỐI LANGFLOW ---
# ID dự án của bạn (đã lấy từ hình ảnh cũ)
FLOW_ID = "f8f2d4a5-78e3-4610-99f4-304da75b54e1"
BASE_API_URL = "http://127.0.0.1:7860"
ENDPOINT = f"{BASE_API_URL}/api/v1/run/{FLOW_ID}"

# 👉 API Key mới của bạn (Đã điền sẵn)
LANGFLOW_API_KEY = "sk-jSmwbPgVKsOOoL1UIQ2PIr4awzF_XGmGQhFqI8i6QRI"

# Cấu hình Tweaks (để mặc định để tránh lỗi logic bên Langflow)
TWEAKS = {
  "ChatInput-KUDM9": {}, 
  "ChatOutput-abc": {}
}

# --- 2. HÀM GỬI TIN NHẮN SANG AI (BACKEND) ---
def run_flow(message: str) -> str:
    """Gửi câu hỏi kèm chìa khóa bảo mật sang Langflow"""
    
    # Đóng gói dữ liệu gửi đi
    payload = {
        "input_value": message,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": TWEAKS
    }
    
    # Kẹp "Vé vào cổng" (API Key) vào đầu gói tin
    headers = {
        "Content-Type": "application/json",
        "x-api-key": LANGFLOW_API_KEY
    }
    
    try:
        # Gửi yêu cầu (POST)
        response = requests.post(ENDPOINT, json=payload, headers=headers)
        
        # Kiểm tra nếu bị chặn (Lỗi 403) hoặc lỗi Server
        response.raise_for_status()
        
        # Lấy kết quả trả về
        response_json = response.json()
        
        # Trích xuất câu trả lời từ cấu trúc JSON phức tạp
        try:
            return response_json["outputs"][0]["outputs"][0]["results"]["message"]["text"]
        except (KeyError, IndexError):
            return "⚠️ Lỗi đọc dữ liệu: Server trả về định dạng lạ. Hãy kiểm tra lại Langflow."
            
    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 403:
            return "⛔ Lỗi 403: Bị từ chối truy cập! Có thể API Key không đúng hoặc User bị khóa."
        return f"❌ Lỗi Server ({err.response.status_code}): {err}"
    except requests.exceptions.ConnectionError:
        return "🔌 Lỗi kết nối: Không tìm thấy Langflow! Bạn đã chạy lệnh 'python -m langflow run' chưa?"
    except Exception as e:
        return f"❌ Có lỗi không xác định: {str(e)}"

# --- 3. GIAO DIỆN NGƯỜI DÙNG (FRONTEND) ---
st.set_page_config(page_title="Tư vấn tuyển sinh TVU", page_icon="🎓", layout="centered")

# [THANH BÊN TRÁI - SIDEBAR]
with st.sidebar:
    try:
        st.image("logo.webp", width=120) # Ảnh logo trường
    except:
        st.info("Chatbot TVU") # Hiện chữ nếu thiếu ảnh
        
    st.header("🗂️ Tùy chọn")
    if st.button("🧹 Xóa cuộc trò chuyện", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.caption("Lịch sử gần đây:")
    # Hiện 3 tin nhắn gần nhất
    if "messages" in st.session_state:
        for msg in st.session_state.messages[-3:]:
            if msg["role"] == "user":
                short = (msg["content"][:30] + '..') if len(msg["content"]) > 30 else msg["content"]
                st.caption(f"👤 {short}")

# [MÀN HÌNH CHÍNH - MAIN]
try:
    st.image("banner.jpg", use_column_width=True) # Ảnh bìa
except:
    pass

st.title("Tư vấn tuyển sinh TVU 2025 🎓")
st.caption("Hệ thống trả lời tự động sử dụng AI (Qwen 2.5) & RAG")

# Khởi tạo lịch sử chat nếu chưa có
if "messages" not in st.session_state:
    st.session_state.messages = []

# Hiển thị lại các tin nhắn cũ trên màn hình
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- XỬ LÝ KHI BẠN NHẬP CÂU HỎI ---
if prompt := st.chat_input("Nhập thắc mắc của bạn (VD: Học phí ngành CNTT?)..."):
    
    # 1. Hiện câu hỏi của bạn ngay lập tức
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Gọi AI trả lời
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("🤖 Trợ lý ảo đang tra cứu thông tin..."):
            # Gọi hàm run_flow ở trên
            full_response = run_flow(prompt)
            
        # 3. Hiệu ứng gõ chữ từng từ (cho sinh động)
        displayed_response = ""
        for word in full_response.split(" "):
            displayed_response += word + " "
            message_placeholder.markdown(displayed_response + "▌")
            time.sleep(0.05) # Tốc độ gõ
            
        message_placeholder.markdown(full_response) # Hiện bản chốt

    # 4. Lưu câu trả lời vào bộ nhớ
    st.session_state.messages.append({"role": "assistant", "content": full_response})