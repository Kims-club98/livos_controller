# control/api_client.py
import os
import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_token():
    token = None
    try:
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
        st.error(f"[{serial_number}] LIVOS_TOKEN 인증 토큰이 설정되지 않았습니다.")
        return False

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    water_val = "ON" if turn_on else "OFF"
    
    # LIVOS API 호환 Payload (Depth 구조 단순화 및 fallback 구조)
    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": water_val
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return True
        else:
            # 실패 원인 화면에 직접 출력 (디버깅용)
            err_msg = f"[{serial_number}] API 에러 ({response.status_code}): {response.text}"
            print(err_msg)
            st.toast(err_msg, icon="⚠️")
            return False
    except Exception as e:
        st.toast(f"[{serial_number}] 통신 예외: {e}", icon="❌")
        return False

def set_water_auto_mode(serial_number: str) -> bool:
    """LIVOS 장비를 AUTO 모드로 전환 (급수 중단 후 자동 제어)"""
    headers = get_headers()
    if "Authorization" not in headers:
        return False

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": "AUTO"
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            return True
        else:
            # AUTO 명령어 미지원 시 OFF 명령으로 fallback 처리
            return send_water_control(serial_number, False)
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