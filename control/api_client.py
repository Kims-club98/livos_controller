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
        if not clean_token.startswith("Token ") and not clean_token.startswith("Bearer "):
            clean_token = f"Token {clean_token}"
        headers["Authorization"] = clean_token
    return headers

def send_water_control(serial_number: str, mode_command: str) -> bool:
    """
    LIVOS 장비 급수 제어 (mode_command: "ON", "OFF", "AUTO")
    """
    headers = get_headers()
    if "Authorization" not in headers:
        st.error(f"[{serial_number}] LIVOS_TOKEN 인증 토큰이 설정되지 않았습니다.")
        return False

    url = f"https://kr.api.livos.io/nanofarm/v1/nanofarm/control?serialNumber={serial_number}"
    
    # 💡 waterLevel 하나에만 ON / OFF / AUTO 전달 (추가 불필요 키 완전 제거)
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
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            res_data = response.json() if response.text else {}
            print(f"[{serial_number}] [{cmd_upper}] 명령 전송 성공: {res_data}")
            return True
        else:
            err_msg = f"[{serial_number}] API 제어 실패 ({response.status_code}): {response.text}"
            print(err_msg)
            st.toast(err_msg, icon="⚠️")
            return False
    except Exception as e:
        st.toast(f"[{serial_number}] 통신 예외: {e}", icon="❌")
        return False

def set_water_auto_mode(serial_number: str) -> bool:
    """LIVOS 장비를 NFT AUTO 모드로 복귀"""
    return send_water_control(serial_number, "AUTO")

def get_device_status(serial_number: str) -> dict:
    """실제 LIVOS 서버에서 장비 상태 조회"""
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