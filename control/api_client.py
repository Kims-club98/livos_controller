# control/api_client.py
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://kr.api.livos.io/nanofarm/v1/nanofarm/control"

# Streamlit Cloud Secrets 우선 참조 -> 로컬 .env 환경변수 차선 참조
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

# 토큰 값이 Bearer로 시작하면 그대로 쓰고, 아니면 'token ' 접두어 활용
if USER_TOKEN and not USER_TOKEN.startswith("Bearer ") and not USER_TOKEN.startswith("token "):
    AUTH_HEADER_VALUE = f"token {USER_TOKEN}" # 만약 기존에 'token 토큰값'으로 성공하셨다면 이 형식을 유지합니다.
else:
    AUTH_HEADER_VALUE = USER_TOKEN if USER_TOKEN else ""

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": AUTH_HEADER_VALUE
}

def send_water_control(serial_number: str, action: str) -> bool:
    if not USER_TOKEN:
        import streamlit as st
        st.error("LIVOS API 토큰이 설정되지 않았습니다. Secrets나 .env를 확인해 주세요.")
        print("[ERROR] USER_TOKEN이 None입니다.")
        return False

    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": action
        }
    }
    
    print(f"\n[SEND] Serial: {serial_number}, Payload: {payload}")
    
    try:
        response = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=5)
        print(f"[RECV] Status Code: {response.status_code}")
        print(f"[RECV] Response Text: {response.text}\n")
        
        if response.status_code != 200:
            import streamlit as st
            st.error(f"[{serial_number}] API 인증 실패 ({response.status_code}): {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR]: {e}")
        import streamlit as st
        st.error(f"[{serial_number}] 통신 예외 발생: {e}")
        return False