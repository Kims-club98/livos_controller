# main.py
import streamlit as st

# 1. st.set_page_config는 최상단 1회 위치
st.set_page_config(
    page_title="LIVOS 급수 통합 제어",
    page_icon="🌱",
    layout="wide"
)

# 2. PWABuilder 호환용 웹 매니페스트 메타 정보 주입
manifest_code = """
<link rel="manifest" href="data:application/manifest+json;base64,ewogICJuYW1lIjogIkxJVk9TIEZhcm0gQ29udHJvbGxlciIsCiAgInNob3J0X25hbWUiIjogIkxJVk9TIiwKICAic3RhcnRfdXJsIjogIi8iLAogICJkaXNwbGF5IjogInN0YW5kYWxvbmUiLAogICJiYWNrZ3JvdW5kX2NvbG9yIjogIiNmOGZhZmMiLAogICJ0aGVtZV9jb2xvciI6ICIjMjJjNTVlIiwKICAiaWNvbnMiOiBbCiAgICB7CiAgICAgICJzcmMiOiAiaHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0tpbXMtY2x1Yjk4L2xpdm9zX2NvbnRyb2xsZXIvbWFpbi9zdGF0aWMvaWNvbi01MTIucG5nIiwKICAgICAgInNpemVzIjogIjUxMng1MTIiLAogICAgICAidHlwZSI6ICJpbWFnZS9wbmciLAogICAgICAicHVycG9zZSI6ICJhbnkgbWFza2FibGUiCiAgICB9CiAgXQp9">
"""
st.markdown(manifest_code, unsafe_allow_html=True)

# 3. 갤럭시/안드로이드 화면 꺼짐 방지(Wake Lock) 스크립트 주입
wake_lock_script = """
<script>
let wakeLock = null;
async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen');
      console.log('Wake Lock 활성화: 화면 꺼짐이 방지됩니다.');
    }
  } catch (err) {
    console.log(`Wake Lock 오류: ${err.name}, ${err.message}`);
  }
}

// 화면 백그라운드 전환 후 복귀 시 자동 재요청
document.addEventListener('visibilitychange', async () => {
  if (wakeLock !== null && document.visibilityState === 'visible') {
    await requestWakeLock();
  }
});

requestWakeLock();
</script>
"""
st.markdown(wake_lock_script, unsafe_allow_html=True)

# 4. 내부 모듈 불러오기
from control.state_manager import init_device_states
from ux.device import render_device_cards

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

from control.state_manager import init_device_states, check_and_auto_off_devices

if "devices" not in st.session_state:
    st.session_state.devices = init_device_states()

# 💡 새로고침이나 복귀 시 시간이 넘은 급수 장비를 자동으로 끄는 체크 로직 호출
check_and_auto_off_devices()