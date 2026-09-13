# control/api_client.py
import os
import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_URL = "https://kr.api.livos.io"

def get_raw_token():
    """Secrets 또는 .env에서 순수 토큰 문자열만 추출"""
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
    
    if token:
        return token.strip().replace("Bearer ", "").replace("Token ", "").strip()
    return None

def send_water_control(serial_number: str, mode_command: str) -> bool:
    """급수 제어 POST 요청"""
    raw_token = get_raw_token()
    if not raw_token:
        st.error(f"[{serial_number}] LIVOS_TOKEN 인증 토큰이 설정되지 않았습니다.")
        return False

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {raw_token}"
    }

    cmd_upper = str(mode_command).upper()
    if cmd_upper not in ["ON", "OFF", "AUTO"]:
        cmd_upper = "OFF"

    # URL 엔드포인트 경로
    control_url = f"{BASE_URL}/nanofarm/v1/control"
    
    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": cmd_upper
        }
    }

    try:
        response = requests.post(control_url, json=payload, headers=headers, timeout=5)
        
        # 화면 진단용 디버그 출력
        with st.expander(f"🔍 [디버그] {serial_number} 통신 로그", expanded=True):
            st.write(f"**URL**: `{control_url}`")
            st.write(f"**Status Code**: `{response.status_code}`")
            st.write("**Payload**:", payload)
            st.write("**Response Text**:", response.text)

        if response.status_code == 200:
            st.toast(f"[{serial_number}] 제어 성공: {cmd_upper}", icon="✅")
            return True
        elif response.status_code == 404:
            st.toast(f"[{serial_number}] 404 경로 오류: control_url 확인 필요", icon="❌")
            return False
        else:
            st.toast(f"[{serial_number}] 제어 실패 ({response.status_code})", icon="⚠️")
            return False
            
    except Exception as e:
        st.error(f"[{serial_number}] 통신 예외 발생: {e}")
        return False

def set_water_auto_mode(serial_number: str) -> bool:
    """자동 모드 설정 래퍼"""
    return send_water_control(serial_number, "AUTO")

def get_device_status(serial_number: str) -> dict:
    """
    state_manager.py에서 임포트하는 장비 상태 조회 GET 함수
    """
    raw_token = get_raw_token()
    if not raw_token:
        return None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {raw_token}"
    }

    status_url = f"{BASE_URL}/nanofarm/v1/nanofarm/status?serialNumber={serial_number}"
    
    try:
        response = requests.get(status_url, headers=headers, timeout=3)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"[{serial_number}] 상태 조회 예외: {e}")
        return None