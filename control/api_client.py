# control/api_client.py
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 반드시 절대 경로(https://...)로 지정해야 Streamlit 내부 경로로 요청되지 않습니다.
BASE_URL = "https://kr.api.livos.io/nanofarm/v1/nanofarm/control"

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

if USER_TOKEN:
    USER_TOKEN = USER_TOKEN.strip()
    if USER_TOKEN.startswith("token "):
        USER_TOKEN = USER_TOKEN.replace("token ", "").strip()
    elif USER_TOKEN.startswith("Bearer "):
        USER_TOKEN = USER_TOKEN.replace("Bearer ", "").strip()

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"token {USER_TOKEN}" if USER_TOKEN else ""
}

def send_water_control(serial_number: str, action: str) -> bool:
    if not USER_TOKEN:
        import streamlit as st
        st.error("❌ LIVOS API 토큰이 설정되지 않았습니다. Secrets나 .env를 확인해 주세요.")
        return False

    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": action
        }
    }
    
    print(f"\n[SEND] Target: {BASE_URL} | Serial: {serial_number}")
    
    try:
        # requests.post 호출 시 BASE_URL이 문자열 그대로 전달되도록 보장
        response = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=5)
        print(f"[RECV] Status Code: {response.status_code}")
        
        if response.status_code != 200:
            import streamlit as st
            st.error(f"[{serial_number}] API 오류 ({response.status_code}): {response.text}")
            return False
            
        return True
    except Exception as e:
        print(f"[ERROR]: {e}")
        import streamlit as st
        st.error(f"[{serial_number}] 통신 예외 발생: {e}")
        return False