import streamlit as st
import base64
from pathlib import Path
from model2 import predict
import tempfile
import os
import plotly.graph_objects as go

st.set_page_config(
    page_title="EEG 집중도 분석기",
    page_icon="🧠",
    layout="centered"
)

if "result" not in st.session_state:
    st.session_state.result = None

def get_logo_base64():
    logo_path = Path(__file__).parent / "logo.png"
    if not logo_path.exists():
        logo_path = Path(__file__).parent / "logo_png.png"
    if logo_path.exists():
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

logo_b64 = get_logo_base64()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
.main { background-color: #f7f7f8; }
.block-container { max-width: 620px; padding-top: 2rem; padding-bottom: 6rem; }

.header-row { display: flex; align-items: flex-end; gap: 14px; margin-bottom: 1.5rem; padding-top: 16px; overflow: visible; }
.header-title { font-size: 1.6rem; font-weight: 700; color: #1f2937; margin: 0; }
.header-logo img { height: 64px; object-fit: contain; display: block; }

/* 카드 스타일 - stVerticalBlock으로 감싸기 */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"]:has(> div[data-testid="element-container"] > div.card-wrap) {
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 14px;
}

.card-title { font-size: 0.78rem; font-weight: 700; color: #6b7280; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
.badge-focus { background: #ede9fe; color: #7c3aed; padding: 3px 14px; border-radius: 20px; font-weight: 700; font-size: 0.95rem; }
.badge-rest { background: #fef3c7; color: #d97706; padding: 3px 14px; border-radius: 20px; font-weight: 700; font-size: 0.95rem; }
.result-row { display: flex; align-items: center; gap: 10px; padding: 4px 0; font-size: 0.95rem; color: #1f2937; margin-bottom: 12px; }
.divider { border: none; border-top: 1px solid #e0e0e0; margin: 14px 0; }
.feedback-text { font-size: 0.92rem; color: #374151; line-height: 1.7; }
.stButton > button { background-color: #059669 !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 700 !important; padding: 0.5rem 1.5rem !important; font-size: 0.95rem !important; }
.stButton > button:disabled { background-color: #e5e7eb !important; color: #9ca3af !important; }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ─────────────────────────────────────────────────
logo_html = f'<div class="header-logo"><img src="data:image/png;base64,{logo_b64}" /></div>' if logo_b64 else ""
st.markdown(f"""
<div class="header-row">
    {logo_html}
    <span class="header-title"> EEG 기반 집중도 분석기 </span>
</div>
""", unsafe_allow_html=True)

# ── 카드 1: 파일 업로드 ──────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="card-title">1. EEG 파일 업로드</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("EEG 파일을 선택하세요", type=["csv", "edf", "txt"])

# ── 카드 2: 분석 시작 ────────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="card-title">2. 분석 시작</div>', unsafe_allow_html=True)
    run = st.button("분석하기  →", disabled=(uploaded_file is None))

if run and uploaded_file is not None:
    with st.spinner("뇌파 신호를 분석하고 있습니다..."):
        suffix = Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        try:
            st.session_state.result = predict(tmp_path)
        finally:
            os.unlink(tmp_path)

# ── 카드 3: 결과 ─────────────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="card-title">3. 예측 결과</div>', unsafe_allow_html=True)

    if st.session_state.result is not None:
        result    = st.session_state.result
        label     = result["label"]
        task_prob = result["task_prob"]
        rest_prob = result["rest_prob"]

        if label == "focus":
            badge = '<span class="badge-focus">Task (집중)</span>'
            msg   = "현재 과제에 집중하고 있을 가능성이 높습니다.<br>현재의 작업 흐름을 유지하세요. 화이팅!"
        else:
            badge = '<span class="badge-rest">Resting (휴식)</span>'
            msg   = "현재 집중 수준이 낮아졌을 가능성이 있습니다.<br>주의 환기를 통해 다시 집중을 유도해 보세요."

        st.markdown(f'<div class="result-row"><span>현재 상태 :</span> {badge}</div>', unsafe_allow_html=True)

        fig = go.Figure(data=[go.Pie(
            labels=["Task (집중)", "Resting (휴식)"],
            values=[task_prob, rest_prob],
            hole=0.6,
            marker=dict(colors=["#7c3aed", "#f59e0b"]),
            textinfo="label+percent",
            textfont=dict(size=13),
            hovertemplate="%{label}: %{value:.1f}%<extra></extra>",
        )])
        fig.update_layout(
            margin=dict(t=60, b=40, l=40, r=40),
            height=280,
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(
                text=f"<b>{task_prob:.1f}%</b><br>집중" if label == "focus" else f"<b>{rest_prob:.1f}%</b><br>휴식",
                x=0.5, y=0.5,
                font=dict(size=16, color="#7c3aed" if label == "focus" else "#f59e0b"),
                showarrow=False
            )]
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">4. 사용자 피드백</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="feedback-text" style="padding-bottom:24px;">{msg}</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div style="color:#9ca3af; font-size:0.92rem; margin-bottom:6px;">현재 상태 : –</div>
        <div style="color:#9ca3af; font-size:0.92rem;">파일을 업로드하고 분석하기 버튼을 눌러주세요.</div>
        <hr class="divider">
        <div class="card-title">4. 사용자 피드백</div>
        <div style="color:#9ca3af; font-size:0.92rem;">파일을 선택하고 분석을 시작해주세요.</div>
        <div style="height:24px;"></div>""", unsafe_allow_html=True)
        
    
