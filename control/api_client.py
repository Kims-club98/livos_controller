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

if USER_TOKEN:
    # 순수 토큰 값만 남기기
    USER_TOKEN = USER_TOKEN.strip().replace("token ", "").replace("Bearer ", "")

def send_water_control(serial_number: str, turn_on: bool) -> bool:
    """LIVOS 장비에 급수 ON/OFF 명령을 전송합니다."""
    if not USER_TOKEN:
        return False

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    # 💡 Boolean(True/False) 대신 서버가 요구하는 String 형태로 변환
    # (서버 사양에 따라 "ON"/"OFF" 또는 "HIGH"/"OFF" 등으로 지정)
    target_status = "ON" if turn_on else "OFF"
    
    payload = {
        "control": {
            "waterLevel": target_status  # String 타입으로 전달 (기존 bool 전달 시 422 에러 발생)
        }
    }

    try:
        response = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"[{serial_number}] 제어 실패 ({response.status_code}): {response.text}")
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
            return response.json() # 서버에서 반환한 상태 객체
        return None
    except Exception as e:
        print(f"[{serial_number}] 상태 조회 실패: {e}")
        return None