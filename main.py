# main.py
import streamlit as st
import time

# 1. Page Config (최상단 1회)
st.set_page_config(
    page_title="LIVOS 급수 통합 제어",
    page_icon="🌱",
    layout="wide"
)

from control.state_manager import (
    init_device_states, 
    check_and_auto_off_devices, 
    sync_with_livos_server,
    stop_all_devices_and_set_nft
)
from control.api_client import send_water_control
from ux.device import render_device_cards

# 세션 상태 초기화 및 최초 1회 서버 동기화
if "devices" not in st.session_state:
    st.session_state.devices = init_device_states()
    sync_with_livos_server()

# 메타 태그 및 Wake Lock 스크립트 주입
manifest_code = """
<link rel="manifest" href="data:application/manifest+json;base64,ewogICJuYW1lIjogIkxJVk9TIEZhcm0gQ29udHJvbGxlciIsCiAgInNob3J0X25hbWUiIjogIkxJVk9TIiwKICAic3RhcnRfdXJsIjogIi8iLAogICJkaXNwbGF5IjogInN0YW5kYWxvbmUiLAogICJiYWNrZ3JvdW5kX2NvbG9yIjogIiNmOGZhZmMiLAogICJ0aGVtZV9jb2xvciI6ICIjMjJjNTVlIiwKICAiaWNvbnMiOiBbCiAgICB7CiAgICAgICJzcmMiOiAiaHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0tpbXMtY2x1Yjk4L2xpdm9zX2NvbnRyb2xsZXIvbWFpbi9zdGF0aWMvaWNvbi01MTIucG5nIiwKICAgICAgInNpemVzIjogIjUxMng1MTIiLAogICAgICAidHlwZSI6ICJpbWFnZS9wbmciLAogICAgICAicHVycG9zZSI6ICJhbnkgbWFza2FibGUiCiAgICB9CiAgXQp9">
"""
st.markdown(manifest_code, unsafe_allow_html=True)

wake_lock_script = """
<script>
let wakeLock = null;
async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen');
    }
  } catch (err) {}
}
document.addEventListener('visibilitychange', async () => {
  if (wakeLock !== null && document.visibilityState === 'visible') {
    await requestWakeLock();
  }
});
requestWakeLock();
</script>
"""
st.markdown(wake_lock_script, unsafe_allow_html=True)

st.title("🚰 LIVOS 급수 제어 대시보드")

# ⚡ 전체 일괄 제어 상단 바
st.markdown("### ⚡ 전체 일괄 제어")
b_col1, b_col2 = st.columns(2)

with b_col1:
    if st.button("💧 전체 강제 급수 시작 (수동 모드 전환)", use_container_width=True):
        with st.spinner("전체 장비에 급수 명령을 전송 중입니다..."):
            for serial, dev in st.session_state.devices.items():
                # 💡 실제 LIVOS API 네트워크 전송 호출
                res = send_water_control(serial, turn_on=True)
                if res:
                    dev["mode"] = "MANUAL"
                    dev["pump_status"] = True
                    dev["start_time"] = time.time()
        st.success("전체 급수 명령 전송 완료")
        st.rerun()

with b_col2:
    if st.button("🚨 전체 긴급 중단 (모두 NFT 모드 복귀)", type="primary", use_container_width=True):
        with st.spinner("전체 장비 급수를 중단합니다..."):
            stop_all_devices_and_set_nft()
        st.success("전체 긴급 중단 완료")
        st.rerun()

st.divider()

# 20개 장비 카드 그리드 출력
render_device_cards()

# 화면 하단 자동 끄기 타이머 체크
check_and_auto_off_devices()