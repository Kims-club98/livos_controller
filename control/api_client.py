# control/api_client.py
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://kr.api.livos.io/nanofarm/v1/nanofarm/control"

# Streamlit Cloud (secrets) 우선 적용 -> 없을 경우 로컬 환경변수 (.env) 사용
# LIVOS_TOKEN 및 LIVOS_USER_TOKEN 모두 지원하도록 설정
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

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {USER_TOKEN}"  # 'token ' 대신 'Bearer ' 표준 형식 사용
}

def send_water_control(serial_number: str, action: str) -> bool:
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
            st.error(f"[{serial_number}] API 호출 실패 ({response.status_code}): {response.text}")
            
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR]: {e}")
        import streamlit as st
        st.error(f"[{serial_number}] 통신 예외 발생: {e}")
        return False