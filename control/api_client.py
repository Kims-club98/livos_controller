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

def get_base_headers():
    token = get_token()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if token:
        clean_token = token.strip()
        # 토큰 접두사 처리 (Token 또는 Bearer)
        if not clean_token.startswith("Token ") and not clean_token.startswith("Bearer "):
            clean_token = f"Token {clean_token}"
        headers["Authorization"] = clean_token
    return headers

def fetch_csrf_token(serial_number: str, session: requests.Session) -> str:
    """GET 요청을 먼저 보내 백엔드 Nginx로부터 x-csrf-token을 추출"""
    headers = get_base_headers()
    status_url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/status?serialNumber={serial_number}"
    
    try:
        res = session.get(status_url, headers=headers, timeout=5)
        csrf_token = res.headers.get("x-csrf-token") or res.headers.get("X-CSRF-Token")
        return csrf_token
    except Exception as e:
        print(f"CSRF 토큰 발급 실패: {e}")
        return None

def send_water_control(serial_number: str, mode_command: str) -> bool:
    """
    LIVOS 장비 급수 제어 (mode_command: "ON", "OFF", "AUTO")
    CSRF 토큰 동적 주입을 통한 403 Forbidden 해결
    """
    session = requests.Session()
    headers = get_base_headers()
    
    if "Authorization" not in headers:
        st.error(f"[{serial_number}] LIVOS_TOKEN 인증 토큰이 설정되지 않았습니다.")
        return False

    # 💡 403 차단 회피: GET 요청을 보내 x-csrf-token 획득
    csrf_token = fetch_csrf_token(serial_number, session)
    if csrf_token:
        headers["x-csrf-token"] = csrf_token
        headers["X-CSRF-Token"] = csrf_token

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    cmd_upper = str(mode_command).upper()
    if cmd_upper not in ["ON", "OFF", "AUTO"]:
        cmd_upper = "OFF"

    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": cmd_upper
        }
    }

    try:
        response = session.post(url, json=payload, headers=headers, timeout=5)
        
        if response.status_code == 200:
            res_data = response.json() if response.text else {}
            st.toast(f"[{serial_number}] 제어 성공: {cmd_upper}", icon="✅")
            return True
        elif response.status_code == 403:
            err_msg = f"[{serial_number}] 403 Forbidden (인증/CSRF 오류). 토큰 권한을 확인하세요."
            print(err_msg)
            st.toast(err_msg, icon="🚫")
            return False
        else:
            err_msg = f"[{serial_number}] API 제어 실패 ({response.status_code}): {response.text}"
            print(err_msg)
            st.toast(err_msg, icon="⚠️")
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

    status_url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/status?serialNumber={serial_number}"
    
    try:
        response = requests.get(status_url, headers=headers, timeout=3)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"[{serial_number}] 상태 조회 예외: {e}")
        return None