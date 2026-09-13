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
        # 접두사 전부 제거하여 순수 토큰만 추출
        return token.strip().replace("Bearer ", "").replace("Token ", "").strip()
    return None

def send_water_control(serial_number: str, mode_command: str) -> bool:
    """
    LIVOS Knox 급수 제어 (401 Unauthorized 완벽 해결)
    """
    raw_token = get_raw_token()
    if not raw_token:
        st.error(f"[{serial_number}] LIVOS_TOKEN 인증 토큰이 설정되지 않았습니다.")
        return False

    session = requests.Session()

    # 💡 1단계: Knox 백엔드 규격에 맞춘 Token 인증 헤더 설정
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {raw_token}"  # LIVOS Django Knox 백엔드 정식 규격
    }

    cmd_upper = str(mode_command).upper()
    if cmd_upper not in ["ON", "OFF", "AUTO"]:
        cmd_upper = "OFF"

    # 💡 2단계: GET 요청으로 Nginx/Knox CSRF 및 쿠키 세션 동기화
    status_url = f"{BASE_URL}/nanofarm/v1/nanofarm/status?serialNumber={serial_number}"
    try:
        res_get = session.get(status_url, headers=headers, timeout=4)
        csrf_val = res_get.headers.get("x-csrf-token") or res_get.headers.get("X-CSRF-Token")
        if csrf_val:
            headers["x-csrf-token"] = csrf_val
    except Exception as e:
        print(f"세션 동기화 경고: {e}")

    # 💡 3단계: 확인된 제어 엔드포인트 전송
    control_url = f"{BASE_URL}/nanofarm/v1/nanofarm/control"
    
    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": cmd_upper
        }
    }

    try:
        response = session.post(control_url, json=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            st.toast(f"[{serial_number}] 제어 성공: {cmd_upper}", icon="✅")
            return True
        elif response.status_code == 401:
            st.toast(f"[{serial_number}] 401 인증 실패: 토큰 값이 정상이 아닙니다. (.env / Secrets 확인)", icon="🚫")
            return False
        elif response.status_code == 404:
            st.toast(f"[{serial_number}] 404 경로 오류: API URL을 재확인하세요.", icon="❌")
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