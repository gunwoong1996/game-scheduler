import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("던파 숙제 스케줄러")
        self.root.geometry("500x600")

        self.tasks = []

        # 입력창 + 추가 버튼 프레임
        entry_frame = tk.Frame(root)
        entry_frame.pack(pady=10)

        self.task_entry = tk.Entry(entry_frame, width=30)
        self.task_entry.grid(row=0, column=0, padx=5)

        add_button = tk.Button(entry_frame, text="숙제 추가", command=self.add_task)
        add_button.grid(row=0, column=1)

        # 리스트박스
        self.task_listbox = tk.Listbox(root, width=60, height=15)
        self.task_listbox.pack(pady=10)

        # 완료 버튼
        done_button = tk.Button(root, text="완료 체크/해제", command=self.mark_done)
        done_button.pack(pady=5)

        # 삭제 버튼
        delete_button = tk.Button(root, text="삭제", command=self.delete_task)
        delete_button.pack(pady=5)

        # 코멘트 프레임
        comment_frame = tk.LabelFrame(root, text="코멘트 (선택한 숙제용)", padx=10, pady=10)
        comment_frame.pack(pady=10, fill="x")

        self.comment_entry = tk.Entry(comment_frame, width=40)
        self.comment_entry.grid(row=0, column=0, padx=5)

        comment_button = tk.Button(comment_frame, text="메모 저장", command=self.save_comment)
        comment_button.grid(row=0, column=1)

        # 코멘트 표시용 라벨
        self.comment_label = tk.Label(root, text="선택된 숙제 메모: 없음", wraplength=400, justify="left")
        self.comment_label.pack(pady=5)

        # 리스트박스 더블클릭 시 코멘트 표시
        self.task_listbox.bind("<Double-1>", self.show_comment)

    def add_task(self):
        task = self.task_entry.get()
        if task:
            self.tasks.append({"task": task, "time": datetime.now(), "done": False, "comment": ""})
            self.update_listbox()
            self.task_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("경고", "숙제를 입력하세요!")

    def update_listbox(self):
        self.task_listbox.delete(0, tk.END)
        for i, t in enumerate(self.tasks, start=1):
            status = "✅" if t["done"] else "❌"
            comment_mark = "📝" if t["comment"] else ""
            self.task_listbox.insert(tk.END, f"{i}. {t['task']} ({status}) {comment_mark}")

    def mark_done(self):
        try:
            selection = self.task_listbox.curselection()[0]
            self.tasks[selection]["done"] = not self.tasks[selection]["done"]  # 토글
            self.update_listbox()
        except IndexError:
            messagebox.showwarning("경고", "숙제를 선택하세요!")

    def delete_task(self):
        try:
            selection = self.task_listbox.curselection()[0]
            del self.tasks[selection]
            self.update_listbox()
            self.comment_label.config(text="선택된 숙제 메모: 없음")
        except IndexError:
            messagebox.showwarning("경고", "삭제할 숙제를 선택하세요!")

    def save_comment(self):
        try:
            selection = self.task_listbox.curselection()[0]
            comment = self.comment_entry.get()
            self.tasks[selection]["comment"] = comment
            self.update_listbox()
            self.comment_label.config(text=f"선택된 숙제 메모: {comment if comment else '없음'}")
            self.comment_entry.delete(0, tk.END)
        except IndexError:
            messagebox.showwarning("경고", "메모를 달 숙제를 선택하세요!")

    def show_comment(self, event):
        try:
            selection = self.task_listbox.curselection()[0]
            comment = self.tasks[selection]["comment"]
            self.comment_label.config(text=f"선택된 숙제 메모: {comment if comment else '없음'}")
        except IndexError:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManager(root)
    root.mainloop()
