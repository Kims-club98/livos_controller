# ux/device.py
import streamlit as st
import time
from control.state_manager import (
    set_manual_water_on, 
    set_nft_auto_mode, 
    process_water_queue
)

def render_timer_card(serial_no, total_seconds):
    """브라우저 localStorage를 활용해 새로고침 후에도 타이머 종료 시각을 유지하는 컴포넌트"""
    timer_script = f"""
    <script>
    const endKey = "timer_end_{serial_no}";
    let endTime = localStorage.getItem(endKey);
    
    // 저장된 종료 시간이 없거나 이미 지난 경우 새로 설정
    if (!endTime || parseInt(endTime) < Date.now()) {{
        endTime = Date.now() + ({total_seconds} * 1000);
        localStorage.setItem(endKey, endTime);
    }}
    
    // 남은 시간 계산 (초 단위)
    const remainingSeconds = Math.max(0, Math.round((parseInt(endTime) - Date.now()) / 1000));
    console.log("[LIVOS Timer] Device {serial_no} Remaining:", remainingSeconds);
    </script>
    """
    st.components.v1.html(timer_script, height=0)

def render_device_cards():
    if "devices" not in st.session_state:
        return

    # --- 상단: 순차 급수 제어 패널 ---
    st.subheader("📋 순차 급수 대기열 제어")
    with st.expander("순차 급수 설정 열기", expanded=True):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            selected_devs = st.multiselect(
                "급수할 기기 선택 (선택 순서대로 실행)",
                options=list(st.session_state.devices.keys()),
                default=[]
            )
            
        with col2:
            minutes = st.number_input("급수 (분)", min_value=0, max_value=60, value=0, step=1)
            
        with col3:
            seconds = st.number_input("급수 (초)", min_value=0, max_value=59, value=30, step=5)
            
        with col4:
            st.write("")
            st.write("")
            if st.button("🚀 순차 급수 시작", type="primary", use_container_width=True):
                total_duration = (minutes * 60) + seconds
                if total_duration <= 0:
                    st.warning("급수 시간을 최소 1초 이상 설정해 주세요.")
                elif selected_devs:
                    process_water_queue(selected_devs, total_duration)
                else:
                    st.warning("급수할 기기를 최소 1개 이상 선택해 주세요.")

    st.divider()

    # --- 하단: 개별 장비 카드 그리드 ---
    cols = st.columns(4)
    for idx, (dev_name, dev_data) in enumerate(st.session_state.devices.items()):
        with cols[idx % 4]:
            with st.container(border=True):
                st.subheader(dev_name)
                
                mode = dev_data.get("mode", "NFT")
                is_active = dev_data.get("water_active", False)
                
                if mode == "MANUAL" and is_active:
                    st.markdown("🟢 **수동 급수 중 (ON)**")
                    
                    # 수동 급수 동작 중일 때 localStorage 기반 타이머 스크립트 실행
                    render_timer_card(dev_name, st.session_state.get(f"duration_{dev_name}", 300))
                    
                    if st.button("⏹ 즉시 중단 (NFT 복귀)", key=f"btn_stop_{dev_name}", type="primary", use_container_width=True):
                        # 중단 시 localStorage 저장값 삭제 스크립트 실행
                        st.components.v1.html(f"<script>localStorage.removeItem('timer_end_{dev_name}');</script>", height=0)
                        set_nft_auto_mode(dev_name, dev_data)
                else:
                    st.markdown("🔵 **NFT 자동 모드 (AUTO)**")
                    if st.button("💧 개별 수동 급수", key=f"btn_on_{dev_name}", type="secondary", use_container_width=True):
                        set_manual_water_on(dev_name, dev_data)