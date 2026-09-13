# control/api_client.py
import os
import requests
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
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

    # 💡 [수정] URL 경로 변경 (/nanofarm 중복 제거)
    control_url = f"{BASE_URL}/nanofarm/v1/control"
    
    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": cmd_upper
        }
    }

    try:
        response = requests.post(control_url, json=payload, headers=headers, timeout=5)
        
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