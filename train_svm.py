# =============================================================
# train_svm.py — SVM-RBF 모델 학습 & 저장
# 전체 48명 데이터로 학습 → svm_model.pkl, scaler.pkl 저장
# =============================================================
import numpy as np
import time, pickle
from pathlib import Path
from scipy.signal import butter, sosfiltfilt, welch
import scipy.stats

# ===== 설정 =====
DATA_DIR   = Path(r"C:\Users\sieun\Desktop\eeg_project\dataset")  # 데이터 경로
MODEL_DIR  = Path("./saved_model")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

FS         = 128
N_CH       = 14

N_SUBJECTS = 48
WIN_SEC    = 2.0
OVERLAP    = 0.5
BAND       = (1.0, 45.0)
LABEL_MAP  = {"lo": 0, "hi": 1}

BANDS = {
    "delta": (1, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta":  (13, 30),
    "gamma": (30, 45),
}

# ===== 전처리 =====
def bandpass_filter(data, fs=FS, low=BAND[0], high=BAND[1], order=4):
    nyq = fs / 2
    sos = butter(order, [low / nyq, high / nyq], btype="band", output="sos")
    return sosfiltfilt(sos, data, axis=0)

def epoch_signal(data, fs=FS, win_sec=WIN_SEC, overlap=OVERLAP):
    win  = int(win_sec * fs)
    step = int(win * (1 - overlap))
    starts = np.arange(0, data.shape[0] - win + 1, step)
    return np.stack([data[s:s + win] for s in starts], axis=0)

def preprocess_file(data):
    return epoch_signal(bandpass_filter(data))

# ===== 특징 추출 =====
def band_powers(epoch_ch, fs=FS):
    f, psd = welch(epoch_ch, fs=fs, nperseg=min(256, len(epoch_ch)))
    integrate = getattr(np, "trapezoid", None) or np.trapz
    powers = []
    for lo, hi in BANDS.values():
        idx = (f >= lo) & (f < hi)
        powers.append(np.log(integrate(psd[idx], f[idx]) + 1e-12))
    return powers

def time_features(epoch_ch):
    return [
        float(np.mean(epoch_ch)),
        float(np.std(epoch_ch)),
        float(scipy.stats.skew(epoch_ch)),
        float(scipy.stats.kurtosis(epoch_ch)),
    ]

def channel_features(epoch_ch, fs=FS):
    bp = band_powers(epoch_ch, fs)
    td = time_features(epoch_ch)
    theta_beta = bp[1] - bp[3]
    alpha_beta = bp[2] - bp[3]
    return bp + td + [theta_beta, alpha_beta]

def extract_features(X, fs=FS):
    N, _, C = X.shape
    feats = np.zeros((N, C * 11), dtype=np.float32)
    for i in range(N):
        row = []
        for c in range(C):
            row.extend(channel_features(X[i, :, c], fs))
        feats[i] = row
    return feats

# ===== 학습 =====
if __name__ == "__main__":
    import sklearn.preprocessing
    from sklearn.svm import SVC
    from sklearn.metrics import accuracy_score

    print("[1/4] 데이터 로드 & 에포킹...")
    t0 = time.time()
    all_epochs, all_labels = [], []
    for sid in range(1, N_SUBJECTS + 1):
        for cond, label in LABEL_MAP.items():
            fpath = DATA_DIR / f"sub{sid:02d}_{cond}.txt"
            data = np.loadtxt(fpath)
            epochs = preprocess_file(data)
            all_epochs.append(epochs)
            all_labels.append(np.full(len(epochs), label, dtype=np.int8))

    X_epoch = np.concatenate(all_epochs, axis=0)
    y_all   = np.concatenate(all_labels, axis=0)
    print(f"    X={X_epoch.shape}, y={y_all.shape}  ({time.time()-t0:.1f}s)")

    print("[2/4] 특징 추출...")
    t0 = time.time()
    F = extract_features(X_epoch)
    print(f"    F={F.shape}  ({time.time()-t0:.1f}s)")

    print("[3/4] SVM-RBF 학습...")
    t0 = time.time()
    scaler = sklearn.preprocessing.StandardScaler()
    F_scaled = scaler.fit_transform(F)

    clf = SVC(kernel="rbf", C=1.0, probability=True)
    clf.fit(F_scaled, y_all)

    train_acc = accuracy_score(y_all, clf.predict(F_scaled))
    print(f"    Train Acc={train_acc:.4f}  ({time.time()-t0:.1f}s)")

    print("[4/4] 모델 저장...")
    with open(MODEL_DIR / "svm_model.pkl", "wb") as f:
        pickle.dump(clf, f)
    with open(MODEL_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    print(f"    저장 완료: {MODEL_DIR / 'svm_model.pkl'}")
    print(f"    저장 완료: {MODEL_DIR / 'scaler.pkl'}")
    print("끝!")
