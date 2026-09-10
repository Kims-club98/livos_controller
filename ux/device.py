# ux/device.py
import streamlit as st
from control.state_manager import (
    set_manual_water_on, 
    set_nft_auto_mode, 
    process_water_queue
)

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
                    if st.button("⏹ 즉시 중단 (NFT 복귀)", key=f"btn_stop_{dev_name}", type="primary", use_container_width=True):
                        set_nft_auto_mode(dev_name, dev_data)
                else:
                    st.markdown("🔵 **NFT 자동 모드 (AUTO)**")
                    if st.button("💧 개별 수동 급수", key=f"btn_on_{dev_name}", type="secondary", use_container_width=True):
                        set_manual_water_on(dev_name, dev_data)