# control/api_client.py
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_token():
    token = None
    try:
        import streamlit as st
        token = (
            st.secrets.get("LIVOS_TOKEN") 
            or st.secrets.get("LIVOS_USER_TOKEN") 
            or os.getenv("LIVOS_TOKEN") 
            or os.getenv("LIVOS_USER_TOKEN")
        )
    except Exception:
        token = os.getenv("LIVOS_TOKEN") or os.getenv("LIVOS_USER_TOKEN")
    return token

def get_headers():
    token = get_token()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if token:
        clean_token = token.strip()
        if not clean_token.startswith("Bearer "):
            clean_token = f"Bearer {clean_token}"
        headers["Authorization"] = clean_token
    return headers

def send_water_control(serial_number: str, turn_on: bool) -> bool:
    """LIVOS 장비에 급수 ON/OFF 명령 전송"""
    headers = get_headers()
    if "Authorization" not in headers:
        print(f"[{serial_number}] 오류: LIVOS_TOKEN이 설정되지 않았습니다.")
        return False

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    # 💡 실제 LIVOS API 명령어 규격 적용 ("ON", "OFF", "AUTO")
    water_val = "ON" if turn_on else "OFF"
    
    payload = {
        "control": {
            "waterLevel": water_val
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return True
        else:
            print(f"[{serial_number}] 급수 제어 실패 ({response.status_code}): {response.text}")
            return False
    except Exception as e:
        print(f"[{serial_number}] API 통신 예외: {e}")
        return False

def set_water_auto_mode(serial_number: str) -> bool:
    """LIVOS 장비를 AUTO 모드로 전환할 때 호출하는 함수"""
    headers = get_headers()
    if "Authorization" not in headers:
        return False

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    payload = {
        "control": {
            "waterLevel": "AUTO"
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"[{serial_number}] AUTO 모드 설정 예외: {e}")
        return False

def get_device_status(serial_number: str) -> dict:
    """실제 LIVOS 서버에서 장비의 현재 상태 조회"""
    headers = get_headers()
    if "Authorization" not in headers:
        return None

    status_url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/status?serialNumber={serial_number}"
    
    try:
        response = requests.get(status_url, headers=headers, timeout=3)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"[{serial_number}] 상태 조회 예외: {e}")
        return None