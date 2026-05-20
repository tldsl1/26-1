import tkinter as tk
from tkinter import filedialog, ttk
import threading
from PIL import Image, ImageTk
import os
from model2 import predict

BG      = "#f7f7f8"
WHITE   = "#ffffff"
BORDER  = "#e0e0e0"
PURPLE  = "#7c3aed"
ORANGE  = "#d97706"
GREEN   = "#059669"
RED     = "#dc2626"
DARK    = "#1f2937"
GRAY    = "#6b7280"
LGRAY   = "#9ca3af"

class EEGApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EEG 집중도 분석기")
        self.geometry("560x660")
        self.resizable(True, True)
        self.configure(bg=BG)
        self.file_path = tk.StringVar(value="")
        self._load_logo()
        self._build_ui()

    def _load_logo(self):
        self.logo_img = None
        try:
            # main2.py와 같은 폴더의 logo.png 로드
            script_dir = os.path.dirname(os.path.abspath(__file__))
            for name in ["logo.png", "logo_png.png"]:
                logo_path = os.path.join(script_dir, name)
                if os.path.exists(logo_path):
                    img = Image.open(logo_path)
                    w, h = img.size
                    new_h = 80
                    new_w = int(w * new_h / h)
                    img = img.resize((new_w, new_h), Image.LANCZOS)
                    self.logo_img = ImageTk.PhotoImage(img)
                    break
        except Exception as e:
            print(f"[로고 로딩 실패] {e}")

    def _card(self, parent, pady=(0, 12)):
        f = tk.Frame(parent, bg=WHITE, bd=0,
                    highlightthickness=1, highlightbackground=BORDER)
        f.pack(fill="x", padx=32, pady=pady, ipady=18)
        return f

    def _label(self, parent, text, size=10, bold=False, color=DARK, anchor="w", pady=2):
        font = ("Apple SD Gothic Neo", size, "bold" if bold else "normal")
        tk.Label(parent, text=text, font=font, bg=WHITE,
                fg=color, anchor=anchor).pack(fill="x", padx=20, pady=pady)

    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(28, 16))

        # 로고 이미지 (있으면 텍스트 왼쪽에 표시)
        if self.logo_img:
            tk.Label(hdr, image=self.logo_img, bg=BG).pack(side="left", padx=(0, 10))
        else:
            tk.Label(hdr, text="🧠", font=("Apple SD Gothic Neo", 16),
                     bg=BG, fg=DARK).pack(side="left")

        tk.Label(hdr, text="EEG 집중도 분석기",
                font=("Apple SD Gothic Neo", 16, "bold"),
                bg=BG, fg=DARK).pack(side="left")

        # 카드 1: 파일 업로드
        c1 = self._card(self)
        self._label(c1, "1.  EEG 파일 업로드", size=10, bold=True, color=GRAY)

        row = tk.Frame(c1, bg=WHITE)
        row.pack(fill="x", padx=20, pady=(4, 0))

        self.path_label = tk.Label(row, text="선택된 파일 없음",
                                font=("Apple SD Gothic Neo", 9),
                                bg="#f3f4f6", fg=LGRAY,
                                anchor="w", padx=10,
                                width=36, relief="flat",
                                highlightthickness=1,
                                highlightbackground=BORDER)
        self.path_label.pack(side="left", ipady=6)

        tk.Button(row, text="  파일 선택  ", command=self._open_file,
                  bg=PURPLE, fg="#ffffff",
                  activebackground="#6d28d9", activeforeground="#ffffff",
                  font=("Apple SD Gothic Neo", 9, "bold"),
                  relief="flat", bd=0, padx=10, pady=6,
                  cursor="hand2").pack(side="left", padx=(8, 0))

        # 카드 2: 분석 시작
        c2 = self._card(self)
        self._label(c2, "2.  분석 시작", size=10, bold=True, color=GRAY)

        self.run_btn = tk.Button(c2, text="  분석하기  →  ",
                                 command=self._run_analysis,
                                 bg="#e5e7eb", fg=LGRAY,
                                 activebackground=GREEN,
                                 activeforeground="#ffffff",
                                 font=("Apple SD Gothic Neo", 10, "bold"),
                                 relief="flat", bd=0, padx=18, pady=8,
                                 cursor="hand2", state="disabled")
        self.run_btn.pack(anchor="w", padx=20, pady=(4, 0))

        # 카드 3: 결과
        c3 = self._card(self, pady=(0, 0))
        self._label(c3, "3.  예측 결과", size=10, bold=True, color=GRAY)

        status_row = tk.Frame(c3, bg=WHITE)
        status_row.pack(fill="x", padx=20, pady=(6, 2))
        tk.Label(status_row, text="현재 상태 : ",
                 font=("Apple SD Gothic Neo", 10),
                 bg=WHITE, fg=DARK).pack(side="left")
        self.status_lbl = tk.Label(status_row, text="–",
                                   font=("Apple SD Gothic Neo", 10, "bold"),
                                   bg=WHITE, fg=LGRAY)
        self.status_lbl.pack(side="left")

        task_row = tk.Frame(c3, bg=WHITE)
        task_row.pack(fill="x", padx=20, pady=1)
        tk.Label(task_row, text="Task 확률   : ",
                 font=("Apple SD Gothic Neo", 10),
                 bg=WHITE, fg=DARK).pack(side="left")
        self.task_lbl = tk.Label(task_row, text="–",
                                 font=("Apple SD Gothic Neo", 10, "bold"),
                                 bg=WHITE, fg=LGRAY)
        self.task_lbl.pack(side="left")

        rest_row = tk.Frame(c3, bg=WHITE)
        rest_row.pack(fill="x", padx=20, pady=1)
        tk.Label(rest_row, text="Resting 확률: ",
                 font=("Apple SD Gothic Neo", 10),
                 bg=WHITE, fg=DARK).pack(side="left")
        self.rest_lbl = tk.Label(rest_row, text="–",
                                 font=("Apple SD Gothic Neo", 10, "bold"),
                                 bg=WHITE, fg=LGRAY)
        self.rest_lbl.pack(side="left")

        tk.Frame(c3, bg=BORDER, height=1).pack(fill="x", padx=20, pady=10)

        self._label(c3, "4.  사용자 피드백", size=10, bold=True, color=GRAY, pady=(0,4))
        self.msg_lbl = tk.Label(c3, text="파일을 선택하고 분석을 시작해주세요.",
                                font=("Apple SD Gothic Neo", 10),
                                bg=WHITE, fg=LGRAY,
                                anchor="w", justify="left",
                                wraplength=460)
        self.msg_lbl.pack(fill="x", padx=20, pady=(0, 6))

        tk.Frame(self, bg=BG, height=20).pack()

    def _open_file(self):
        path = filedialog.askopenfilename(
            title="뇌파 파일 선택",
            filetypes=[("EEG files", "*.csv *.edf *.txt"), ("All", "*.*")]
        )
        if path:
            self.file_path.set(path)
            short = path.split("/")[-1]
            self.path_label.config(text=f"  {short}", fg=DARK)
            self.run_btn.config(state="normal", bg=GREEN, fg="#ffffff",
                                activebackground="#047857")

    def _run_analysis(self):
        self.run_btn.config(state="disabled", text="  분석 중...  ")
        self.status_lbl.config(text="분석 중...", fg=ORANGE)
        self.task_lbl.config(text="–", fg=LGRAY)
        self.rest_lbl.config(text="–", fg=LGRAY)
        self.msg_lbl.config(text="뇌파 신호를 분석하고 있습니다...", fg=LGRAY)
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        result = predict(self.file_path.get())
        self.after(0, self._show_result, result)

    def _show_result(self, result):
        label      = result["label"]
        task_prob  = result["task_prob"]
        rest_prob  = result["rest_prob"]

        if label == "focus":
            status_text  = "Task (집중)"
            status_color = PURPLE
            msg = "현재 과제에 집중하고 있을 가능성이 높습니다. \n 현재의 작업 흐름을 유지하되, 피로감이 느껴지면 짧은 휴식을 권장합니다."
        else:
            status_text  = "Resting (휴식)"
            status_color = ORANGE
            msg = "현재 집중 수준이 낮아졌을 가능성이 있습니다. \n 짧은 휴식이나 주의 환기를 통해 다시 집중을 유도해 보세요."

        self.status_lbl.config(text=status_text, fg=status_color)
        self.task_lbl.config(text=f"{task_prob:.1f}%", fg=PURPLE)
        self.rest_lbl.config(text=f"{rest_prob:.1f}%", fg=ORANGE)
        self.msg_lbl.config(text=msg, fg=DARK)
        self.run_btn.config(state="normal", text="  다시 분석  →  ",
                            bg=GREEN, fg="#ffffff")

if __name__ == "__main__":
    app = EEGApp()
    app.mainloop()