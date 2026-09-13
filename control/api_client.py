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

    # 💡 1시도: Query Parameter 형태로 전송 (Spring Boot @RequestParam 대응)
    query_url = f"{BASE_URL}/nanofarm/v1/nanofarm/control?serialNumber={serial_number}&waterLevel={cmd_upper}&control={cmd_upper}"
    
    payload = {
        "serialNumber": serial_number,
        "waterLevel": cmd_upper,
        "control": {
            "waterLevel": cmd_upper
        }
    }

    try:
        # Query Param + POST 요청
        response = requests.post(query_url, json=payload, headers=headers, timeout=5)
        
        # 404 발생 시 GET 요청 구조 시도
        if response.status_code == 404:
            response = requests.get(query_url, headers=headers, timeout=5)

        with st.expander(f"🔍 [디버그] {serial_number} 통신 로그", expanded=True):
            st.write(f"**요청 URL**: `{response.url}`")
            st.write(f"**Status Code**: `{response.status_code}`")
            st.write("**Response Text**:", response.text)

        if response.status_code == 200:
            st.toast(f"[{serial_number}] 제어 성공: {cmd_upper}", icon="✅")
            return True
        elif response.status_code == 404:
            st.toast(f"[{serial_number}] 404 경로 오류: API 백엔드 라우팅 매핑을 확인해 주세요.", icon="❌")
            return False
        else:
            st.toast(f"[{serial_number}] 제어 실패 ({response.status_code})", icon="⚠️")
            return False
            
    except Exception as e:
        st.error(f"[{serial_number}] 통신 예외 발생: {e}")
        return False

def set_water_auto_mode(serial_number: str) -> bool:
    return send_water_control(serial_number, "AUTO")

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