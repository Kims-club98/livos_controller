# control/api_client.py
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

# Headers 설정 (Bearer 토큰 포함)
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

if USER_TOKEN:
    clean_token = USER_TOKEN.strip().replace("token ", "").replace("Bearer ", "")
    HEADERS["Authorization"] = f"Bearer {clean_token}"

def send_water_control(serial_number: str, turn_on: bool) -> bool:
    """LIVOS 장비에 급수 ON/OFF 명령을 전송합니다."""
    if not USER_TOKEN:
        print(f"[{serial_number}] 오류: LIVOS_TOKEN이 설정되지 않았습니다.")
        return False

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    # 💡 String Type 요구사항에 맞춘 정확한 수위 문자열 설정 ("HIGH" / "OFF")
    water_val = "HIGH" if turn_on else "OFF"
    
    payload = {
        "control": {
            "waterLevel": water_val
        }
    }

    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"[{serial_number}] 급수 제어 실패 ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"[{serial_number}] API 통신 예외: {e}")
        return False

def get_device_status(serial_number: str) -> dict:
    """실제 LIVOS 서버에서 장비의 현재 상태(급수 여부 등)를 조회합니다."""
    if not USER_TOKEN:
        return None

    status_url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/status?serialNumber={serial_number}"
    
    try:
        response = requests.get(status_url, headers=HEADERS, timeout=3)
        if response.status_code == 200:
            return response.json()
        print(f"[{serial_number}] 상태 조회 실패 ({response.status_code}): {response.text}")
        return None
    except Exception as e:
        print(f"[{serial_number}] 상태 조회 예외: {e}")
        return None