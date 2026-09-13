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

# 토큰 정리 및 Headers 구성
HEADERS = {"Content-Type": "application/json"}
if USER_TOKEN:
    clean_token = USER_TOKEN.strip().replace("token ", "").replace("Bearer ", "")
    HEADERS["Authorization"] = f"Bearer {clean_token}"

def send_water_control(serial_number: str, turn_on: bool) -> bool:
    """LIVOS 장비에 급수 ON/OFF 명령을 전송합니다."""
    if not USER_TOKEN:
        print(f"[{serial_number}] 오류: LIVOS_TOKEN이 설정되지 않았습니다.")
        return False

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    # LIVOS API 요구 규격: String 타입 ("HIGH" 또는 "OFF")
    water_level_val = "HIGH" if turn_on else "OFF"
    
    payload = {
        "control": {
            "waterLevel": water_level_val
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
            return response.json()
        return None
    except Exception as e:
        print(f"[{serial_number}] 상태 조회 실패: {e}")
        return None