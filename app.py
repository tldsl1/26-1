import streamlit as st
import base64
from pathlib import Path
from model2 import predict
import tempfile
import os

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="EEG 집중도 분석기",
    page_icon="🧠",
    layout="centered"
)

# ── 로고 base64 변환 함수 ────────────────────────────────
def get_logo_base64():
    logo_path = Path(__file__).parent / "logo.png"
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "logo_png.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()

# ── 커스텀 CSS ───────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
}

.main { background-color: #f7f7f8; }

.block-container {
    max-width: 600px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

.logo-top-right {
    position: fixed;
    top: 14px;
    right: 24px;
    z-index: 9999;
}

.logo-top-right img {
    height: 52px;
    object-fit: contain;
}

.page-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 1.5rem;
}

.card {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 14px;
}

.card-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #6b7280;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.result-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 0;
    font-size: 0.95rem;
    color: #1f2937;
}

.result-label { color: #1f2937; min-width: 110px; }

.badge-focus {
    background: #ede9fe;
    color: #7c3aed;
    padding: 3px 12px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
}

.badge-rest {
    background: #fef3c7;
    color: #d97706;
    padding: 3px 12px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
}

.prob-focus { color: #7c3aed; font-weight: 700; }
.prob-rest  { color: #d97706; font-weight: 700; }

.divider {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 14px 0;
}

.feedback-text {
    font-size: 0.92rem;
    color: #374151;
    line-height: 1.7;
}

.stButton > button {
    background-color: #059669 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 700 !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    padding: 0.5rem 1.5rem !important;
    font-size: 0.95rem !important;
    cursor: pointer !important;
}

.stButton > button:disabled {
    background-color: #e5e7eb !important;
    color: #9ca3af !important;
}
</style>
""", unsafe_allow_html=True)

# ── 오른쪽 상단 로고 ─────────────────────────────────────
if logo_b64:
    st.markdown(f"""
    <div class="logo-top-right">
        <img src="data:image/png;base64,{logo_b64}" />
    </div>
    """, unsafe_allow_html=True)

# ── 헤더 타이틀 ──────────────────────────────────────────
st.markdown('<div class="page-title">🧠 EEG 집중도 분석기</div>', unsafe_allow_html=True)

# ── 카드 1: 파일 업로드 ──────────────────────────────────
st.markdown('<div class="card"><div class="card-title">1. EEG 파일 업로드</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("EEG 파일을 선택하세요", type=["csv", "edf", "txt"])
st.markdown('</div>', unsafe_allow_html=True)

# ── 카드 2: 분석 시작 ────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">2. 분석 시작</div>', unsafe_allow_html=True)
run = st.button("분석하기  →", disabled=(uploaded_file is None))
st.markdown('</div>', unsafe_allow_html=True)

# ── 카드 3: 결과 ─────────────────────────────────────────
st.markdown('<div class="card"><div class="card-title">3. 예측 결과</div>', unsafe_allow_html=True)

if run and uploaded_file is not None:
    with st.spinner("뇌파 신호를 분석하고 있습니다..."):
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        try:
            result = predict(tmp_path)
        finally:
            os.unlink(tmp_path)

    label     = result["label"]
    task_prob = result["task_prob"]
    rest_prob = result["rest_prob"]

    if label == "focus":
        badge = '<span class="badge-focus">Task (집중)</span>'
        msg   = "현재 과제에 집중하고 있을 가능성이 높습니다.<br>현재의 작업 흐름을 유지하되, 피로감이 느껴지면 짧은 휴식을 권장합니다."
    else:
        badge = '<span class="badge-rest">Resting (휴식)</span>'
        msg   = "현재 집중 수준이 낮아졌을 가능성이 있습니다.<br>짧은 휴식이나 주의 환기를 통해 다시 집중을 유도해 보세요."

    st.markdown(f"""
    <div class="result-row">
        <span class="result-label">현재 상태 :</span> {badge}
    </div>
    <div class="result-row">
        <span class="result-label">Task 확률 :</span>
        <span class="prob-focus">{task_prob:.1f}%</span>
    </div>
    <div class="result-row">
        <span class="result-label">Resting 확률 :</span>
        <span class="prob-rest">{rest_prob:.1f}%</span>
    </div>
    <hr class="divider">
    <div class="card-title">4. 사용자 피드백</div>
    <div class="feedback-text">{msg}</div>
    """, unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="color:#9ca3af; font-size:0.92rem;">현재 상태 : –</div>
    <div style="color:#9ca3af; font-size:0.92rem;">Task 확률 : –</div>
    <div style="color:#9ca3af; font-size:0.92rem;">Resting 확률 : –</div>
    <hr class="divider">
    <div class="card-title">4. 사용자 피드백</div>
    <div style="color:#9ca3af; font-size:0.92rem;">파일을 선택하고 분석을 시작해주세요.</div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
