# 2026년도 1학기 캡스톤 디자인
- 과제명: EEG 기반 집중도 분석 웹 사이트 구축
- 팀 명: 박박김
- 팀 대표: 박소희
- 지도교수: 최가영 교수님

# 프로젝트 내용
- 목적
  14채널 EEG 신호를 활용하여 Resting(안정) 상태와 Task(과제 수행) 상태를 자동으로 분류하는 시스템을 구축한다. EEG 기반 인지 상태 판별의 최적 파이프라인을 도출하는 것을 목표로 한다.

# 데이터셋
- 피험자 수: 48명
- 조건: Resting(lo), Task(hi) - 피험자당 2개 파일
- 총 파일 수: 96개(sub01_lo.txt ~ sub48_hi.txt)
- 채널 수: 14채널
- 샘플링 주파수: 128Hz
- 기록 길이: 150초(19,200 samples)
- 채널 배치: 14채널은 국제 10-20 시스템 기반으로 배치되며, 전두엽(Frontal), 측두엽(Temporal), 두정엽(Parietal), 후두엽(Occipital) 영역을 포함한다.
AF3, F7, F3, FC5, T7, P7, O1, O2, P8, T8, FC6, F4, F8, AF4

# 프로젝트 구조
eeg_project/
- ├── app.py # Streamlit 웹 인터페이스 
- ├── model2.py # SVM 모델 로드 & predict() 함수
- ├── train_svm.py # 모델 학습 & 저장 스크립트
- ├── compare_ml_eegnet.py # LOSO 검증 (SVM vs EEGNet 비교)
- ├── saved_model/
- │ ├── svm_model.pkl # 학습된 SVM-RBF 모델
- │ └── scaler.pkl # StandardScaler 정규화 기준
- ├── dataset/ # EEG 데이터 (sub01~48_hi/lo.txt)
- └── README.md

# 시스템 구조
- 원시 EEG 신호 (14채널, 128Hz)

- 밴드패스 필터 (1~45Hz)

- 에포킹 (2초 윈도우, 50% 오버랩)

- 특징 추출 (154차원)

- StandardScaler 정규화

- SVM-RBF 분류 → Task / Resting 확률 출력

