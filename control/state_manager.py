# control/state_manager.py
import time
import streamlit as st
from control.api_client import send_water_control, get_device_status

SERIAL_MAP = {
    "정식기 1호": "gr04dec103h1dd",
    "정식기 2호": "gr04dec103h101",
    "정식기 3호": "gr04dec103h103",
    "정식기 4호": "gr04dec103h104",
    "정식기 5호": "gr04dec103h105",
    "정식기 6호": "gr04dec103h106",
    "정식기 7호": "gr04dec103h107",
    "정식기 8호": "gr04dec103h108",
    "정식기 9호": "gr04dec103h109",
    "정식기 10호": "gr04dec103h110",
    "정식기 11호": "gr04dec103h111",
    "정식기 12호": "gr04dec103h112",
    "정식기 13호": "gr04dec103h113",
    "정식기 14호": "gr04dec103h114",
    "정식기 15호": "gr04dec103h115",
    "정식기 16호": "gr04dec103h116",
    "정식기 17호": "gr04dec103h117",
    "정식기 18호": "gr04dec103h118",
    "이식기 1호": "gr04dec103h119",
    "이식기 2호": "gr04dec103h120",
}

def init_device_states():
    """20개 장비 초기 상태 및 타이머 세션 초기화"""
    devices = {}
    for name, serial in SERIAL_MAP.items():
        dev_type = "정식기" if "정식기" in name else "이식기"
        devices[name] = {
            "type": dev_type,
            "serial": serial,
            "mode": "NFT",
            "water_active": False,
            "end_timestamp": None
        }
    return devices

def format_time(seconds: int) -> str:
    """초 단위 시간을 문자열로 변환"""
    minutes = max(0, seconds) // 60
    rem_seconds = max(0, seconds) % 60
    if minutes > 0:
        return f"{minutes}분 {rem_seconds}초"
    return f"{rem_seconds}초"

def set_manual_water_on(device_name: str, device_data: dict, duration_seconds: int = 0):
    serial = device_data["serial"]
    # 💡 "ON" 문자열 직접 전달
    success = send_water_control(serial, "ON")
    
    if success:
        device_data["mode"] = "MANUAL"
        device_data["water_active"] = True
        if duration_seconds > 0:
            device_data["end_timestamp"] = time.time() + duration_seconds
        st.success(f"[{device_name}] 수동 급수가 시작되었습니다.")
        st.rerun()
    else:
        st.error(f"[{device_name}] 수동 급수 시작 실패")

def set_nft_auto_mode(device_name: str, device_data: dict):
    serial = device_data["serial"]
    
    # 💡 1단계: 급수 중단 ("OFF")
    res1 = send_water_control(serial, "OFF")
    time.sleep(0.3)
    
    # 💡 2단계: NFT 자동 모드 전환 ("AUTO")
    res2 = send_water_control(serial, "AUTO")
    
    if res1 and res2:
        device_data["mode"] = "NFT"
        device_data["water_active"] = False
        device_data["end_timestamp"] = None
        st.success(f"[{device_name}] 급수 종료 및 NFT 모드 복귀")
        st.rerun()
    else:
        st.error(f"[{device_name}] NFT 모드 복귀 실패")

def check_and_auto_off_devices():
    """시간이 만료된 장비를 감지하여 자동 꺼짐 처리"""
    if "devices" not in st.session_state:
        return

    now = time.time()
    for name, dev in st.session_state.devices.items():
        if dev.get("water_active") and dev.get("end_timestamp"):
            if now >= dev["end_timestamp"]:
                send_water_control(dev["serial"], "OFF")
                time.sleep(0.3)
                send_water_control(dev["serial"], "AUTO")
                dev["mode"] = "NFT"
                dev["water_active"] = False
                dev["end_timestamp"] = None
                st.toast(f"⏰ [{name}] 설정된 급수 시간이 완료되어 NFT 모드로 복귀했습니다.")

def process_water_queue(selected_devices: list, duration_seconds: int):
    """대기열 순차 급수 처리"""
    total_count = len(selected_devices)
    status_area = st.empty()
    progress_bar = st.progress(0, text="순차 급수 준비 중...")

    for idx, dev_name in enumerate(selected_devices):
        dev_data = st.session_state.devices[dev_name]
        serial = dev_data["serial"]

        status_area.info(
            f"⏳ [{idx + 1}/{total_count}] **{dev_name}** 급수 진행 중... "
            f"(총 설정 시간: {format_time(duration_seconds)})"
        )
        
        if send_water_control(serial, "ON"):
            dev_data["mode"] = "MANUAL"
            dev_data["water_active"] = True
            dev_data["end_timestamp"] = time.time() + duration_seconds
            
            for sec in range(duration_seconds):
                time.sleep(1)
                remaining_sec = duration_seconds - (sec + 1)
                overall_progress = (idx + (sec + 1) / duration_seconds) / total_count
                
                time_str = format_time(remaining_sec)
                progress_bar.progress(
                    overall_progress, 
                    text=f"[{dev_name}] 남은 시간: {time_str} (전체 진행률: {int(overall_progress * 100)}%)"
                )
            
            send_water_control(serial, "OFF")
            time.sleep(0.3)
            send_water_control(serial, "AUTO")
            
            dev_data["mode"] = "NFT"
            dev_data["water_active"] = False
            dev_data["end_timestamp"] = None
        else:
            status_area.error(f"❌ [{dev_name}] 급수 시작 실패. 다음 기기로 이동합니다.")
            time.sleep(1)

    status_area.success(f"✅ 총 {total_count}개 기기의 순차 급수 작업이 완료되었습니다!")
    progress_bar.empty()
    time.sleep(2)
    st.rerun()

def sync_with_livos_server():
    """수동 급수 중인 상태를 지키며 LIVOS 상태 동기화"""
    if "devices" not in st.session_state:
        return

    for dev_name, dev_data in st.session_state.devices.items():
        if dev_data.get("water_active") and dev_data.get("end_timestamp"):
            continue
            
        try:
            server_info = get_device_status(dev_data["serial"])
            if server_info:
                # 백엔드의 waterLevel 응답값 체크
                w_level = str(server_info.get("waterLevel", "")).upper()
                is_watering = w_level == "ON" or server_info.get("waterActive", False)
                dev_data["water_active"] = is_watering
                if is_watering:
                    dev_data["mode"] = "MANUAL"
        except Exception as e:
            print(f"[{dev_name}] 동기화 실패: {e}")

def stop_all_devices_and_set_nft():
    """모든 장비 급수 즉시 중단"""
    if "devices" not in st.session_state:
        return

    for dev_name, dev_data in st.session_state.devices.items():
        try:
            send_water_control(dev_data["serial"], "OFF")
            time.sleep(0.1)
            send_water_control(dev_data["serial"], "AUTO")
        except Exception as e:
            print(f"[{dev_name}] 긴급 중단 API 실패: {e}")

        dev_data["mode"] = "NFT"
        dev_data["water_active"] = False
        dev_data["end_timestamp"] = None

    if "water_queue" in st.session_state:
        st.session_state.water_queue = []
    
    st.toast("🚨 모든 장치의 급수가 중단되고 NFT 자동 모드로 전환되었습니다.", icon="🛑")