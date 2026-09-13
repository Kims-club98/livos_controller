# control/api_client.py
import os
import time  # 💡 대기시간 처리를 위해 추가
import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_URL = "https://kr.api.livos.io"

def get_raw_token():
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
    """
    LIVOS 정식기 급수 제어 API 호출
    """
    raw_token = get_raw_token()
    if not raw_token:
        st.error(f"[{serial_number}] LIVOS_TOKEN 인증 토큰이 설정되지 않았습니다.")
        return False

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {raw_token}"
    }

    cmd_lower = str(mode_command).lower().strip()
    if cmd_lower not in ["on", "off", "auto"]:
        cmd_lower = "off"

    control_url = f"{BASE_URL}/nanofarm/v1/nanofarm/control"
    
    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": cmd_lower
        }
    }

    try:
        response = requests.post(control_url, json=payload, headers=headers, timeout=5)
        
        with st.expander(f"🔍 [디버그 로그] {serial_number}", expanded=True):
            st.write(f"**URL**: `{control_url}`")
            st.write(f"**Status Code**: `{response.status_code}`")
            st.write("**전송 Payload**:", payload)
            st.write("**서버 응답**: ", response.text)

        if response.status_code == 200:
            # 💡 [핵심] 하드웨어 동기화 및 DB 반영을 위해 1.5초 대기
            time.sleep(1.5)
            st.toast(f"[{serial_number}] 제어 명령 전송 성공: {cmd_lower}", icon="✅")
            return True
        else:
            st.toast(f"[{serial_number}] 제어 실패 (응답 코드: {response.status_code})", icon="⚠️")
            return False
            
    except Exception as e:
        st.error(f"[{serial_number}] 통신 예외 발생: {e}")
        return False

def set_water_auto_mode(serial_number: str) -> bool:
    return send_water_control(serial_number, "auto")

def get_device_status(serial_number: str) -> dict:
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