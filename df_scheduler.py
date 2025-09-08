import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os
import sys

# 실행파일이든, py 파일이든 "현재 실행 중인 파일의 위치"를 기준으로 저장 경로 설정
if getattr(sys, 'frozen', False):  # 실행파일로 빌드된 경우
    BASE_DIR = os.path.dirname(sys.executable)
else:  # 파이썬 스크립트로 실행하는 경우
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SAVE_FILE = os.path.join(BASE_DIR, "tasks.json")

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("던파 숙제 스케줄러 (포터블)")
        self.root.geometry("700x600")

        # 데이터 구조 기본값
        self.tasks = {
            "공통": {"공통": []},
            "1군": {},
            "2군": {},
            "3군": {},
            "4군": {}
        }

        # 저장된 데이터 불러오기
        self.load_data()

        self.current_group = None
        self.current_character = None

        # 프레임 배치
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10)

        # 그룹별 캐릭터 선택 UI
        self.group_frames = {}
        self.char_selectors = {}

        for group in ["공통", "1군", "2군", "3군", "4군"]:
            frame = tk.LabelFrame(top_frame, text=group, padx=10, pady=5)
            frame.pack(side=tk.LEFT, padx=5)
            self.group_frames[group] = frame

            if group == "공통":
                self.char_selectors[group] = ttk.Combobox(frame, values=["공통"], state="readonly", width=10)
                self.char_selectors[group].set("공통")
                self.char_selectors[group].pack()
            else:
                self.char_selectors[group] = ttk.Combobox(frame, values=list(self.tasks[group].keys()), state="readonly", width=10)
                self.char_selectors[group].pack()

                add_btn = tk.Button(frame, text="캐릭터 추가", command=lambda g=group: self.add_character(g))
                add_btn.pack(pady=2)

            self.char_selectors[group].bind("<<ComboboxSelected>>", lambda e, g=group: self.switch_character(g))

        # 작업 관리 프레임
        task_frame = tk.Frame(root)
        task_frame.pack(pady=10)

        self.task_listbox = tk.Listbox(task_frame, width=70, height=15)
        self.task_listbox.pack(pady=5)

        entry_frame = tk.Frame(task_frame)
        entry_frame.pack()

        self.task_entry = tk.Entry(entry_frame, width=40)
        self.task_entry.grid(row=0, column=0, padx=5)

        add_button = tk.Button(entry_frame, text="숙제 추가", command=self.add_task)
        add_button.grid(row=0, column=1)

        # 버튼 프레임
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)

        done_button = tk.Button(button_frame, text="선택 숙제 완료/해제", command=self.mark_done)
        done_button.grid(row=0, column=0, padx=5)

        comment_button = tk.Button(button_frame, text="코멘트 추가/보기", command=self.add_comment)
        comment_button.grid(row=0, column=1, padx=5)

        delete_button = tk.Button(button_frame, text="숙제 삭제", command=self.delete_task)
        delete_button.grid(row=0, column=2, padx=5)

        mark_all_button = tk.Button(button_frame, text="전체 완료/해제", command=self.toggle_all_tasks)
        mark_all_button.grid(row=0, column=3, padx=5)

        # 종료 시 자동 저장
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def add_character(self, group):
        name = simpledialog.askstring("캐릭터 추가", f"{group}에 추가할 캐릭터 이름을 입력하세요:")
        if name and name not in self.tasks[group]:
            self.tasks[group][name] = []
            self.char_selectors[group]["values"] = list(self.tasks[group].keys())
            self.char_selectors[group].set(name)
            self.switch_character(group)
            self.save_data()

    def switch_character(self, group):
        char = self.char_selectors[group].get()
        self.current_group = group
        self.current_character = char
        self.update_listbox()

    def add_task(self):
        if not self.current_group or not self.current_character:
            messagebox.showwarning("경고", "캐릭터를 먼저 선택하세요!")
            return
        task = self.task_entry.get()
        if task:
            self.tasks[self.current_group][self.current_character].append({"task": task, "done": False, "comment": ""})
            self.update_listbox()
            self.task_entry.delete(0, tk.END)
            self.save_data()

    def update_listbox(self):
        self.task_listbox.delete(0, tk.END)
        if self.current_group and self.current_character:
            for i, t in enumerate(self.tasks[self.current_group][self.current_character], start=1):
                status = "✅" if t["done"] else "❌"
                comment = f" (메모: {t['comment']})" if t["comment"] else ""
                self.task_listbox.insert(tk.END, f"{i}. {t['task']} {status}{comment}")

    def mark_done(self):
        try:
            selection = self.task_listbox.curselection()[0]
            task = self.tasks[self.current_group][self.current_character][selection]
            task["done"] = not task["done"]
            self.update_listbox()
            self.save_data()
        except:
            messagebox.showwarning("경고", "숙제를 선택하세요!")

    def add_comment(self):
        try:
            selection = self.task_listbox.curselection()[0]
            task = self.tasks[self.current_group][self.current_character][selection]
            comment = simpledialog.askstring("코멘트", "메모를 입력하세요:", initialvalue=task["comment"])
            if comment is not None:
                task["comment"] = comment
            self.update_listbox()
            self.save_data()
        except:
            messagebox.showwarning("경고", "숙제를 선택하세요!")

    def delete_task(self):
        try:
            selection = self.task_listbox.curselection()[0]
            del self.tasks[self.current_group][self.current_character][selection]
            self.update_listbox()
            self.save_data()
        except:
            messagebox.showwarning("경고", "삭제할 숙제를 선택하세요!")

    def toggle_all_tasks(self):
        if not self.current_group or not self.current_character:
            messagebox.showwarning("경고", "캐릭터를 먼저 선택하세요!")
            return
        char_tasks = self.tasks[self.current_group][self.current_character]
        if all(t["done"] for t in char_tasks):
            for t in char_tasks:
                t["done"] = False
        else:
            for t in char_tasks:
                t["done"] = True
        self.update_listbox()
        self.save_data()

    def save_data(self):
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("에러", f"저장 실패: {e}")

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except:
                messagebox.showwarning("경고", "저장된 데이터를 불러올 수 없습니다.")

    def on_close(self):
        self.save_data()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManager(root)
    root.mainloop()
