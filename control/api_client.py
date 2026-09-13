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

    # 💡 1. 사용자 지정 정식 엔드포인트 URL
    control_url = f"{BASE_URL}/nanofarm/v1/nanofarm/control"
    
    # 💡 2. 호환용 Payload 구성 (루트 필드 & 객체 필드 동시 지원)
    payload = {
        "serialNumber": serial_number,
        "waterLevel": cmd_upper,
        "control": {
            "waterLevel": cmd_upper
        }
    }

    try:
        # 💡 Spring Boot의 REST 규격에 따라 PUT 우선 시도 후 POST 순차 시도
        response = requests.put(control_url, json=payload, headers=headers, timeout=5)
        
        # PUT으로 405 Method Not Allowed나 404가 뜨면 POST로 재시도
        if response.status_code in [404, 405]:
            response = requests.post(control_url, json=payload, headers=headers, timeout=5)

        # 화면 디버그 로그 출력
        with st.expander(f"🔍 [디버그] {serial_number} 통신 로그", expanded=True):
            st.write(f"**URL**: `{control_url}`")
            st.write(f"**Status Code**: `{response.status_code}`")
            st.write("**Payload**:", payload)
            st.write("**Response Text**:", response.text)

        if response.status_code == 200:
            st.toast(f"[{serial_number}] 제어 성공: {cmd_upper}", icon="✅")
            return True
        elif response.status_code == 404:
            # 💡 URL 경로에 시리얼번호가 들어가는 RESTful Path 형태 2차 시도
            alt_url = f"{BASE_URL}/nanofarm/v1/nanofarm/{serial_number}/control"
            alt_res = requests.post(alt_url, json={"waterLevel": cmd_upper}, headers=headers, timeout=5)
            
            if alt_res.status_code == 200:
                st.toast(f"[{serial_number}] 제어 성공 (Path 매핑): {cmd_upper}", icon="✅")
                return True
            
            st.toast(f"[{serial_number}] 404 경로/매핑 오류", icon="❌")
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