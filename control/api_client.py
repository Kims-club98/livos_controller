# control/api_client.py
import os
import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 💡 절대 경로 Base URL 명시 (Streamlit 호스트로의 잘못된 요청 차단)
BASE_URL = "https://kr.api.livos.io"

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

def get_base_headers():
    token = get_token()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if token:
        clean_token = token.strip()
        raw_token = clean_token.replace("Bearer ", "").replace("Token ", "").strip()
        
        # 💡 Knox Gateway 표준 인증 헤더 세팅
        headers["Authorization"] = f"Bearer {raw_token}"
        headers["x-knox-token"] = raw_token
        headers["knox-token"] = raw_token
        headers["X-Access-Token"] = raw_token
        
    return headers

def send_water_control(serial_number: str, mode_command: str) -> bool:
    """
    LIVOS Knox 백엔드 절대 경로 제어 요청
    """
    session = requests.Session()
    headers = get_base_headers()
    
    if "Authorization" not in headers:
        st.error(f"[{serial_number}] LIVOS_TOKEN 인증 토큰이 설정되지 않았습니다.")
        return False

    # 💡 Streamlit 앱 도메인이 아닌 kr.api.livos.io 절대 경로 지정
    url = f"{BASE_URL}/nanofarm/v1/nanofarm/control"
    
    cmd_upper = str(mode_command).upper()
    if cmd_upper not in ["ON", "OFF", "AUTO"]:
        cmd_upper = "OFF"

    payload = {
        "serialNumber": serial_number,
        "waterLevel": cmd_upper,
        "control": {
            "waterLevel": cmd_upper
        }
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            st.toast(f"[{serial_number}] 제어 성공: {cmd_upper}", icon="✅")
            return True
        elif response.status_code == 401:
            st.toast(f"[{serial_number}] 401 Unauthorized: Knox 인증 토큰을 확인하세요.", icon="🚫")
            return False
        elif response.status_code == 404:
            st.toast(f"[{serial_number}] 404 Error: API 엔드포인트를 찾을 수 없습니다.", icon="❌")
            return False
        else:
            st.toast(f"[{serial_number}] 제어 실패 ({response.status_code}): {response.text}", icon="⚠️")
            return False
            
    except Exception as e:
        st.toast(f"[{serial_number}] 통신 예외: {e}", icon="❌")
        return False

def set_water_auto_mode(serial_number: str) -> bool:
    return send_water_control(serial_number, "AUTO")

def get_device_status(serial_number: str) -> dict:
    headers = get_base_headers()
    if "Authorization" not in headers:
        return None

    status_url = f"{BASE_URL}/nanofarm/v1/nanofarm/status?serialNumber={serial_number}"
    
    try:
        response = requests.get(status_url, headers=headers, timeout=3)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"[{serial_number}] 상태 조회 예외: {e}")
        return None