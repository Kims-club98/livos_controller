# streamlit 앱 실행파일
# main.py
import streamlit as st
from control.state_manager import init_device_states
from ux.device import render_device_cards

st.set_page_config(page_title="LIVOS 급수 통합 제어", layout="wide")

st.title("🚰 LIVOS 급수 제어 대시보드")

# 세션 상태 초기화
if "devices" not in st.session_state:
    st.session_state.devices = init_device_states()

# 전체 일괄 급수 제어 상단 바
st.markdown("### ⚡ 전체 일괄 제어")
b_col1, b_col2 = st.columns(2)

with b_col1:
    if st.button("💧 전체 강제 급수 시작 (수동 모드 전환)", use_container_width=True):
        for dev in st.session_state.devices.values():
            dev["mode"] = "MANUAL"
            dev["pump_status"] = True
        st.rerun()

with b_col2:
    if st.button("🔄 전체 NFT 모드로 복귀 (급수 중단)", use_container_width=True):
        for dev in st.session_state.devices.values():
            dev["mode"] = "NFT"
            dev["pump_status"] = False
        st.rerun()

st.divider()

# 20개 장비 카드 그리드 출력
render_device_cards()

## 실행
# python -m streamlit run main.py