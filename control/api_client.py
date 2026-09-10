# control/api_client.py
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://kr.api.livos.io/nanofarm/v1/nanofarm/control"

# 1. Streamlit Cloud Secrets 또는 .env에서 토큰 가져오기
USER_TOKEN = None
try:
    import streamlit as st
    USER_TOKEN = (
        st.secrets.get("LIVOS_TOKEN") 
        or st.secrets.get("LIVOS_USER_TOKEN") 
        or os.getenv("LIVOS_TOKEN") 
        or os.getenv("LIVOS_USER_TOKEN")
    )
except Exception:
    USER_TOKEN = os.getenv("LIVOS_TOKEN") or os.getenv("LIVOS_USER_TOKEN")

# 토큰 값 앞뒤 공백 및 혹시 붙어있을 접두어 정리
if USER_TOKEN:
    USER_TOKEN = USER_TOKEN.strip()
    if USER_TOKEN.startswith("token "):
        USER_TOKEN = USER_TOKEN.replace("token ", "").strip()
    elif USER_TOKEN.startswith("Bearer "):
        USER_TOKEN = USER_TOKEN.replace("Bearer ", "").strip()

# 2. 'token {TOKEN}' 규격 적용
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"token {USER_TOKEN}" if USER_TOKEN else ""
}

def send_water_control(serial_number: str, action: str) -> bool:
    if not USER_TOKEN:
        import streamlit as st
        st.error("❌ LIVOS API 토큰이 설정되지 않았습니다. Secrets나 .env를 확인해 주세요.")
        print("[ERROR] USER_TOKEN이 None입니다.")
        return False

    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": action  # "on", "off", "auto"
        }
    }
    
    print(f"\n[SEND] Serial: {serial_number}, Payload: {payload}")
    print(f"[AUTH] Header: {HEADERS['Authorization'][:12]}...")
    
    try:
        response = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=5)
        print(f"[RECV] Status Code: {response.status_code}")
        print(f"[RECV] Response Text: {response.text}\n")
        
        if response.status_code != 200:
            import streamlit as st
            st.error(f"[{serial_number}] API 호출 실패 ({response.status_code}): {response.text}")
            return False
            
        return True
    except Exception as e:
        print(f"[ERROR]: {e}")
        import streamlit as st
        st.error(f"[{serial_number}] 통신 예외 발생: {e}")
        return False