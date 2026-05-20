# =============================================================
# model2.py — SVM-RBF 서비스용 predict 함수
# saved_model/svm_model.pkl, scaler.pkl 로드 → 실시간 예측
# =============================================================
import numpy as np
import pickle
from pathlib import Path
from scipy.signal import butter, sosfiltfilt, welch
from scipy.stats import skew, kurtosis

# ===== 설정 =====
MODEL_DIR = Path(__file__).parent / "saved_model"
FS        = 128
WIN_SEC   = 2.0
OVERLAP   = 0.5
BAND      = (1.0, 45.0)

BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta":  (13, 30),
    "gamma": (30, 45),
}

# ===== 모델 로드 (앱 시작 시 1회) =====
_clf    = pickle.load(open(MODEL_DIR / "svm_model.pkl", "rb"))
_scaler = pickle.load(open(MODEL_DIR / "scaler.pkl", "rb"))

# ===== 전처리 =====
def _bandpass(data):
    nyq = FS / 2
    sos = butter(4, [BAND[0]/nyq, BAND[1]/nyq], btype="band", output="sos")
    return sosfiltfilt(sos, data, axis=0)

def _epoch(data):
    win  = int(WIN_SEC * FS)
    step = int(win * (1 - OVERLAP))
    starts = np.arange(0, data.shape[0] - win + 1, step)
    return np.stack([data[s:s + win] for s in starts], axis=0)

# ===== 특징 추출 =====
def _band_powers(ch):
    f, psd = welch(ch, fs=FS, nperseg=min(256, len(ch)))
    integrate = getattr(np, "trapezoid", None) or np.trapz
    return [np.log(integrate(psd[(f >= lo) & (f < hi)],
                             f[(f >= lo) & (f < hi)]) + 1e-12)
            for lo, hi in BANDS.values()]

def _channel_features(ch):
    bp = _band_powers(ch)
    td = [float(np.mean(ch)), float(np.std(ch)),
          float(skew(ch)), float(kurtosis(ch))]
    return bp + td + [bp[1]-bp[3], bp[2]-bp[3]]

def _extract_features(X):
    N, _, C = X.shape
    feats = np.zeros((N, C * 11), dtype=np.float32)
    for i in range(N):
        row = []
        for c in range(C):
            row.extend(_channel_features(X[i, :, c]))
        feats[i] = row
    return feats

# ===== 파일 로드 =====
def _load_eeg(file_path: str) -> np.ndarray:
    """CSV/TXT → (samples, channels) ndarray"""
    ext = Path(file_path).suffix.lower()
    if ext in (".csv", ".txt"):
        data = np.loadtxt(file_path, delimiter="," if ext == ".csv" else None)
        if data.ndim == 1:
            raise ValueError("단일 채널 데이터는 지원하지 않습니다. (14채널 필요)")
        return data
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")

# ===== 메인 predict 함수 =====
def predict(file_path: str) -> dict:
    """
    EEG 파일 → SVM-RBF 예측 결과
    반환: { label, task_prob, rest_prob }

    - 파일을 에포킹 → 특징 추출 → 전체 에포크 확률 평균
    - task_prob ≥ 50 → "focus", 아니면 "rest"
    """
    raw    = _load_eeg(file_path)
    filt   = _bandpass(raw)
    epochs = _epoch(filt)              # (N_epochs, 256, 14)
    feats  = _extract_features(epochs) # (N_epochs, 154)
    feats  = _scaler.transform(feats)

    probs  = _clf.predict_proba(feats) # (N_epochs, 2) → [rest, task]
    mean_p = probs.mean(axis=0)        # 전체 에포크 평균

    rest_prob = round(float(mean_p[0]) * 100, 1)
    task_prob = round(float(mean_p[1]) * 100, 1)
    label     = "focus" if task_prob >= 50 else "rest"

    return {"label": label, "task_prob": task_prob, "rest_prob": rest_prob}
