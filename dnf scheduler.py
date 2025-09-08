import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("던파 숙제 스케줄러")
        self.root.geometry("400x500")

        self.tasks = []

        # 입력창
        self.task_entry = tk.Entry(root, width=30)
        self.task_entry.pack(pady=10)

        # 추가 버튼
        add_button = tk.Button(root, text="숙제 추가", command=self.add_task)
        add_button.pack()

        # 리스트박스
        self.task_listbox = tk.Listbox(root, width=50, height=15)
        self.task_listbox.pack(pady=10)

        # 완료 버튼
        done_button = tk.Button(root, text="완료 체크", command=self.mark_done)
        done_button.pack()

        # 삭제 버튼
        delete_button = tk.Button(root, text="삭제", command=self.delete_task)
        delete_button.pack()

    def add_task(self):
        task = self.task_entry.get()
        if task:
            self.tasks.append({"task": task, "time": datetime.now(), "done": False})
            self.update_listbox()
            self.task_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("경고", "숙제를 입력하세요!")

    def update_listbox(self):
        self.task_listbox.delete(0, tk.END)
        for i, t in enumerate(self.tasks, start=1):
            status = "✅" if t["done"] else "❌"
            self.task_listbox.insert(tk.END, f"{i}. {t['task']} ({status})")

    def mark_done(self):
        try:
            selection = self.task_listbox.curselection()[0]
            self.tasks[selection]["done"] = True
            self.update_listbox()
        except IndexError:
            messagebox.showwarning("경고", "숙제를 선택하세요!")

    def delete_task(self):
        try:
            selection = self.task_listbox.curselection()[0]
            del self.tasks[selection]
            self.update_listbox()
        except IndexError:
            messagebox.showwarning("경고", "삭제할 숙제를 선택하세요!")

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManager(root)
    root.mainloop()
