# control/api_client.py
import os
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_URL = "https://kr.api.livos.io/nanofarm/v1/nanofarm/control"

USER_TOKEN = None
try:
    import streamlit as st
    USER_TOKEN = (
        st.secrets.get("LIVOS_TOKEN") 
        or st.secrets.get("LIVOS_USER_TOKEN") 
        or os.getenv("LIVOS_TOKEN") 
        or os.getenv("LIVOS_USER_TOKEN")
    )
except Exception:
    USER_TOKEN = os.getenv("LIVOS_TOKEN") or os.getenv("LIVOS_USER_TOKEN")

if USER_TOKEN:
    # 순수 토큰 값만 남기기
    USER_TOKEN = USER_TOKEN.strip().replace("token ", "").replace("Bearer ", "")

def send_water_control(serial_number: str, action: str) -> bool:
    if not USER_TOKEN:
        import streamlit as st
        st.error("❌ LIVOS API 토큰이 설정되지 않았습니다.")
        return False

    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": action
        }
    }
    
    # Knox Token 호환성을 위해 3가지 표준 포맷으로 시도
    auth_formats = [
        f"Bearer {USER_TOKEN}",
        f"token {USER_TOKEN}",
        USER_TOKEN
    ]
    
    for auth_val in auth_formats:
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_val
        }
        
        try:
            response = requests.post(BASE_URL, json=payload, headers=headers, timeout=5)
            print(f"[TRY AUTH] Header: {auth_val[:10]}... | Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"[SUCCESS] 시리얼: {serial_number} 급수 제어 성공!")
                return True
            elif response.status_code != 401:
                # 401 이외의 에러(예: 400, 404 등)는 토큰 형식이 아닌 파라미터 문제이므로 중단
                import streamlit as st
                st.error(f"[{serial_number}] API 에러 ({response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR]: {e}")
            
    # 3가지 방식 모두 401 실패 시 출력
    import streamlit as st
    st.error(f"[{serial_number}] 인증 실패 (401): 토큰 값이 만료되었거나 올바르지 않습니다.")
    return False