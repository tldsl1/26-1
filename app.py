# =============================================================
# app.py — Streamlit 웹 버전 EEG 집중도 분석기
# 실행: streamlit run app.py
# =============================================================
import streamlit as st
import tempfile
import os
from model2 import predict

st.set_page_config(page_title="EEG 집중도 분석기", page_icon="🧠", layout="centered")

# ── CSS 스타일 ──
st.markdown("""
<style>
    .main { max-width: 700px; margin: auto; }
    .result-box {
        background: #f8f9fa;
        border-radius: 16px;
        padding: 30px;
        text-align: center;
        margin: 20px 0;
    }
    .prob-bar {
        background: #e9ecef;
        border-radius: 10px;
        height: 32px;
        margin: 8px 0;
        overflow: hidden;
    }
    .prob-fill-task {
        background: linear-gradient(90deg, #7c3aed, #a78bfa);
        height: 100%;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 14px;
    }
    .prob-fill-rest {
        background: linear-gradient(90deg, #d97706, #fbbf24);
        height: 100%;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ── 헤더 ──
st.markdown("# 🧠 EEG 집중도 분석기")
st.markdown("뇌파(EEG) 신호를 분석하여 **집중 / 휴식** 상태를 판별합니다.")
st.divider()

# ── 파일 업로드 ──
st.markdown("### 1. EEG 파일 업로드")
uploaded = st.file_uploader(
    "CSV 또는 TXT 파일을 올려주세요",
    type=["csv", "txt"],
    help="14채널 EEG 데이터 파일 (샘플링 주파수 128Hz)"
)

# ── 분석 ──
if uploaded is not None:
    st.success(f"✅ 파일 선택 완료: **{uploaded.name}**")

    st.markdown("### 2. 분석 시작")
    if st.button("🔍  분석하기", type="primary", use_container_width=True):

        # 임시 파일 저장 (predict 함수가 파일 경로를 받으므로)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1]) as tmp:
            tmp.write(uploaded.getvalue())
            tmp_path = tmp.name

        with st.spinner("뇌파 신호를 분석하고 있습니다..."):
            result = predict(tmp_path)

        os.unlink(tmp_path)  # 임시 파일 삭제

        # ── 결과 표시 ──
        st.markdown("### 3. 예측 결과")

        label     = result["label"]
        task_prob = result["task_prob"]
        rest_prob = result["rest_prob"]

        if label == "focus":
            icon    = "🎯"
            status  = "Task (집중)"
            color   = "#7c3aed"
            message = "현재 과제에 집중하고 있을 가능성이 높습니다. \n 현재의 작업 흐름을 유지하되, 피로감이 느껴지면 짧은 휴식을 권장합니다."
        else:
            icon    = "😌"
            status  = "Resting (휴식)"
            color   = "#d97706"
            message = "현재 집중 수준이 낮아졌을 가능성이 있습니다. \n 짧은 휴식이나 주의 환기를 통해 다시 집중을 유도해 보세요."

        # 결과 카드
        st.markdown(f"""
        <div class="result-box">
            <div style="font-size: 60px;">{icon}</div>
            <div style="font-size: 28px; font-weight: bold; color: {color}; margin: 10px 0;">
                {status}
            </div>
            <div style="font-size: 16px; color: #374151; white-space: pre-line;">
                {message}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 확률 바
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Task (집중) 확률**")
            st.markdown(f"""
            <div class="prob-bar">
                <div class="prob-fill-task" style="width: {task_prob}%;">{task_prob}%</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("**Resting (휴식) 확률**")
            st.markdown(f"""
            <div class="prob-bar">
                <div class="prob-fill-rest" style="width: {rest_prob}%;">{rest_prob}%</div>
            </div>
            """, unsafe_allow_html=True)

        # ── 피드백 ──
        st.divider()
        st.markdown("### 4. 사용자 피드백")
        if label == "focus":
            st.info("💡 현재 높은 집중 상태입니다. 이 상태를 유지하며 작업을 이어가세요!")
        else:
            st.warning("💡 집중도가 낮은 상태입니다. 5~10분 휴식 후 다시 시도해보세요.")

else:
    st.info("👆 위에서 EEG 파일을 업로드해주세요.")

# ── 푸터 ──
st.divider()
st.caption("EEG 집중도 분석기 | SVM-RBF 기반 | 14채널 Emotiv EPOC")
