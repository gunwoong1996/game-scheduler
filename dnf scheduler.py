import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("던파 숙제 스케줄러")
        self.root.geometry("700x600")

        # 데이터 구조: {group: {character: [tasks...]}}
        self.tasks = {
            "공통": {"공통": []},
            "1군": {},
            "2군": {},
            "3군": {},
            "4군": {}
        }

        # 현재 선택된 그룹 & 캐릭터
        self.current_group = None
        self.current_character = None

        # 프레임 배치
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10)

        # 그룹별 캐릭터 선택 프레임
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

            # 캐릭터 선택 이벤트
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

    def add_character(self, group):
        name = simpledialog.askstring("캐릭터 추가", f"{group}에 추가할 캐릭터 이름을 입력하세요:")
        if name and name not in self.tasks[group]:
            self.tasks[group][name] = []
            self.char_selectors[group]["values"] = list(self.tasks[group].keys())
            self.char_selectors[group].set(name)
            self.switch_character(group)

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
        except:
            messagebox.showwarning("경고", "숙제를 선택하세요!")

    def delete_task(self):
        try:
            selection = self.task_listbox.curselection()[0]
            del self.tasks[self.current_group][self.current_character][selection]
            self.update_listbox()
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

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManager(root)
    root.mainloop()
