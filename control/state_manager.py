# control/state_manager.py
import time
import streamlit as st
from control.api_client import send_water_control

# 20개 장비 시리얼 번호 1:1 매핑
SERIAL_MAP = {
    # 정식기 1~18호
    "정식기 1호": "gr04dec103h1dd",
    "정식기 2호": "gr04dec103h101",
    "정식기 3호": "gr04dec103h103",
    "정식기 4호": "gr04dec103h104",
    "정식기 5호": "gr04dec103h105",  # 실제 값으로 수정
    "정식기 6호": "gr04dec103h106",  # 실제 값으로 수정
    "정식기 7호": "gr04dec103h107",  # 실제 값으로 수정
    "정식기 8호": "gr04dec103h108",  # 실제 값으로 수정
    "정식기 9호": "gr04dec103h109",  # 실제 값으로 수정
    "정식기 10호": "gr04dec103h110", # 실제 값으로 수정
    "정식기 11호": "gr04dec103h111", # 실제 값으로 수정
    "정식기 12호": "gr04dec103h112", # 실제 값으로 수정
    "정식기 13호": "gr04dec103h113", # 실제 값으로 수정
    "정식기 14호": "gr04dec103h114", # 실제 값으로 수정
    "정식기 15호": "gr04dec103h115", # 실제 값으로 수정
    "정식기 16호": "gr04dec103h116", # 실제 값으로 수정
    "정식기 17호": "gr04dec103h117", # 실제 값으로 수정
    "정식기 18호": "gr04dec103h118", # 실제 값으로 수정
    
    # 이식기 1~2호
    "이식기 1호": "gr04dec103h119",
    "이식기 2호": "gr04dec103h120",
}

def init_device_states():
    """20개 장비 초기 상태 설정 (기본: NFT 모드 / 급수 OFF)"""
    devices = {}
    for name, serial in SERIAL_MAP.items():
        dev_type = "정식기" if "정식기" in name else "이식기"
        devices[name] = {
            "type": dev_type,
            "serial": serial,
            "mode": "NFT",           # "NFT" 또는 "MANUAL"
            "water_active": False    # True(급수 중) / False(급수 대기)
        }
    return devices

def set_manual_water_on(device_name: str, device_data: dict):
    serial = device_data["serial"]
    success = send_water_control(serial, "on")
    
    if success:
        device_data["mode"] = "MANUAL"
        device_data["water_active"] = True
        st.success(f"[{device_name}] 수동 급수가 시작되었습니다.")
        st.rerun()
    else:
        st.error(f"[{device_name}] 수동 급수 시작 실패")

def set_nft_auto_mode(device_name: str, device_data: dict):
    serial = device_data["serial"]
    
    # 1단계: 급수 중단 ('off')
    res1 = send_water_control(serial, "off")
    time.sleep(0.3)
    
    # 2단계: NFT 자동 모드 전환 ('auto')
    res2 = send_water_control(serial, "auto")
    
    if res1 and res2:
        device_data["mode"] = "NFT"
        device_data["water_active"] = False
        st.success(f"[{device_name}] 급수 종료 및 NFT 모드 복귀")
        st.rerun()
    else:
        st.error(f"[{device_name}] NFT 모드 복귀 실패")
        
def run_timed_irrigation(device_name: str, device_data: dict, duration_seconds: int):
    """
    타이머 급수 제어:
    1. 수동 급수 시작 ('on')
    2. 지정된 시간(duration_seconds) 동안 대기
    3. 급수 종료 ('off')
    4. NFT 자동 모드 복귀 ('auto')
    """
    serial = device_data["serial"]
    
    # 1단계: 수동 급수 시작
    if send_water_control(serial, "on"):
        device_data["mode"] = "MANUAL"
        device_data["water_active"] = True
        
        # UI 안내 및 대기 (진행 바 표시)
        progress_text = f"[{device_name}] {duration_seconds}초 동안 수동 급수 진행 중..."
        progress_bar = st.progress(0, text=progress_text)
        
        for i in range(duration_seconds):
            time.sleep(1)
            progress_bar.progress((i + 1) / duration_seconds, text=progress_text)
            
        progress_bar.empty()
        
        # 2단계: 급수 종료 ('off')
        res1 = send_water_control(serial, "off")
        time.sleep(0.3)
        
        # 3단계: NFT 자동 모드 복귀 ('auto')
        res2 = send_water_control(serial, "auto")
        
        if res1 and res2:
            device_data["mode"] = "NFT"
            device_data["water_active"] = False
            st.success(f"[{device_name}] {duration_seconds}초 타이머 급수 완료 및 NFT 모드 복귀!")
            st.rerun()
        else:
            st.error(f"[{device_name}] NFT 모드 자동 복귀 실패. 수동 확인 필요.")
    else:
        st.error(f"[{device_name}] 수동 급수 시작 실패.")

def process_water_queue(selected_devices: list, duration_seconds: int):
    """
    대기열(Queue)에 등록된 기기들을 순차적으로 급수 처리
    selected_devices: 예) ["정식기 1호", "정식기 2호", "정식기 3호"]
    """
    total_count = len(selected_devices)
    status_area = st.empty()
    progress_bar = st.progress(0, text="순차 급수 준비 중...")

    for idx, dev_name in enumerate(selected_devices):
        dev_data = st.session_state.devices[dev_name]
        serial = dev_data["serial"]

        # 1. 상태 업데이트 및 안내
        status_area.info(f"⏳ [{idx + 1}/{total_count}] **{dev_name}** 급수 진행 중... (남은 대기 기기: {total_count - idx - 1}개)")
        
        # 2. 수동 급수 시작 ('on')
        if send_water_control(serial, "on"):
            dev_data["mode"] = "MANUAL"
            dev_data["water_active"] = True
            
            # 3. 설정된 시간만큼 진행
            for sec in range(duration_seconds):
                time.sleep(1)
                overall_progress = (idx + (sec + 1) / duration_seconds) / total_count
                progress_bar.progress(
                    overall_progress, 
                    text=f"[{dev_name}] {duration_seconds - sec}초 남음 (전체 진행률: {int(overall_progress * 100)}%)"
                )
            
            # 4. 급수 종료 ('off') 및 NFT 복귀 ('auto')
            send_water_control(serial, "off")
            time.sleep(0.3)
            send_water_control(serial, "auto")
            
            dev_data["mode"] = "NFT"
            dev_data["water_active"] = False
        else:
            status_area.error(f"❌ [{dev_name}] 급수 시작 실패. 다음 기기로 이동합니다.")
            time.sleep(1)

    status_area.success(f"✅ 총 {total_count}개 기기의 순차 급수 작업이 완료되었습니다!")
    progress_bar.empty()
    time.sleep(2)
    st.rerun()

def format_time(seconds: int) -> str:
    """초 단위 시간을 'N분 M초' 또는 'M초' 형태의 문자열로 변환"""
    minutes = seconds // 60
    rem_seconds = seconds % 60
    if minutes > 0:
        return f"{minutes}분 {rem_seconds}초"
    return f"{rem_seconds}초"

def process_water_queue(selected_devices: list, duration_seconds: int):
    """
    대기열(Queue)에 등록된 기기들을 순차적으로 급수 처리 (분/초 표시 적용)
    """
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
        
        # 1. 수동 급수 시작 ('on')
        if send_water_control(serial, "on"):
            dev_data["mode"] = "MANUAL"
            dev_data["water_active"] = True
            
            # 2. 지정된 시간만큼 타이머 수행
            for sec in range(duration_seconds):
                time.sleep(1)
                remaining_sec = duration_seconds - (sec + 1)
                overall_progress = (idx + (sec + 1) / duration_seconds) / total_count
                
                # '1분 30초 남음' 형식으로 표시
                time_str = format_time(remaining_sec)
                progress_bar.progress(
                    overall_progress, 
                    text=f"[{dev_name}] 남은 시간: {time_str} (전체 진행률: {int(overall_progress * 100)}%)"
                )
            
            # 3. 급수 종료 ('off') 및 NFT 복귀 ('auto')
            send_water_control(serial, "off")
            time.sleep(0.3)
            send_water_control(serial, "auto")
            
            dev_data["mode"] = "NFT"
            dev_data["water_active"] = False
        else:
            status_area.error(f"❌ [{dev_name}] 급수 시작 실패. 다음 기기로 이동합니다.")
            time.sleep(1)

    status_area.success(f"✅ 총 {total_count}개 기기의 순차 급수 작업이 완료되었습니다!")
    progress_bar.empty()
    time.sleep(2)
    st.rerun()