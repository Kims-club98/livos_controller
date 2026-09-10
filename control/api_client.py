# control/api_client.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://kr.api.livos.io/nanofarm/v1/nanofarm/control"

# 1년 유지 토큰 값 입력 (Bearer 토큰 형태)
USER_TOKEN = os.getenv("LIVOS_TOKEN")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"token {USER_TOKEN}"
}

def send_water_control(serial_number: str, action: str) -> bool:
    payload = {
        "serialNumber": serial_number,
        "control": {
            "waterLevel": action
        }
    }
    
    # 디버깅 출력: 실제 보낸 Payload 확인
    print(f"\n[SEND] Serial: {serial_number}, Payload: {payload}")
    
    try:
        response = requests.post(BASE_URL, json=payload, headers=HEADERS, timeout=5)
        print(f"[RECV] Status Code: {response.status_code}")
        print(f"[RECV] Response Text: {response.text}\n") # 서버에서 돌려준 실제 응답 내용 출력
        
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR]: {e}")
        return False