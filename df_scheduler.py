import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os
import sys

# 포터블 경로 설정
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "tasks.json")

GROUP_COLORS = {
    "공통": "lightgray",
    "1군": "lightgreen",
    "2군": "lightyellow",
    "3군": "orange",
    "4군": "tomato"
}

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("던파 숙제 스케줄러 + 벞교 파티")
        self.root.geometry("900x600")

        # 기본 데이터 구조
        self.tasks = {"공통": {"공통":[]}, "1군": {}, "2군": {}, "3군": {}, "4군": {}}
        self.parties = {}
        self.load_data()

        self.current_group = None
        self.current_character = None
        self.current_party = None

        # --- UI 구성 ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=10)

        self.group_frames = {}
        self.char_selectors = {}

        for group in ["공통","1군","2군","3군","4군"]:
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

        # 벞교 파티 프레임
        party_frame = tk.LabelFrame(root, text="벞교 파티", padx=10, pady=5)
        party_frame.pack(pady=5)
        self.party_selector = ttk.Combobox(party_frame, values=list(self.parties.keys()), state="readonly", width=30)
        self.party_selector.pack(side=tk.LEFT, padx=5)
        self.party_selector.bind("<<ComboboxSelected>>", lambda e: self.switch_party())
        party_add_btn = tk.Button(party_frame, text="파티 추가", command=self.add_party)
        party_add_btn.pack(side=tk.LEFT, padx=5)
        party_edit_btn = tk.Button(party_frame, text="파티 편집", command=self.edit_party_members)
        party_edit_btn.pack(side=tk.LEFT, padx=5)

        # 검색/필터
        filter_frame = tk.Frame(root)
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="검색:").pack(side=tk.LEFT)
        self.filter_entry = tk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="적용", command=self.apply_filter).pack(side=tk.LEFT)
        tk.Button(filter_frame, text="초기화", command=self.update_listbox).pack(side=tk.LEFT, padx=5)

        # 숙제 리스트
        self.task_listbox = tk.Listbox(root, width=100, height=20)
        self.task_listbox.pack(pady=5)

        entry_frame = tk.Frame(root)
        entry_frame.pack()
        self.task_entry = tk.Entry(entry_frame, width=60)
        self.task_entry.grid(row=0, column=0, padx=5)
        add_button = tk.Button(entry_frame, text="숙제 추가", command=self.add_task)
        add_button.grid(row=0, column=1)

        # 버튼
        button_frame = tk.Frame(root)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="선택 숙제 완료/해제", command=self.mark_done).grid(row=0,column=0,padx=5)
        tk.Button(button_frame, text="코멘트 추가/보기", command=self.add_comment).grid(row=0,column=1,padx=5)
        tk.Button(button_frame, text="숙제 삭제", command=self.delete_task).grid(row=0,column=2,padx=5)
        tk.Button(button_frame, text="전체 완료/해제", command=self.toggle_all_tasks).grid(row=0,column=3,padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.switch_character("공통")

    # --- 캐릭터 및 파티 ---
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
        self.current_party = None
        self.party_selector.set('')
        self.update_listbox()

    def add_party(self):
        name = simpledialog.askstring("파티 추가", "파티 이름을 입력하세요:")
        if not name: return
        members = simpledialog.askstring("파티 구성", "캐릭터 이름을 ','로 구분 입력 (예: 버퍼,딜러1,딜러2,딜러3):")
        if members:
            self.parties[name] = [m.strip() for m in members.split(",")]
            self.party_selector["values"] = list(self.parties.keys())
            self.party_selector.set(name)
            self.switch_party()
            self.save_data()

    def switch_party(self):
        party = self.party_selector.get()
        if party in self.parties:
            self.current_party = party
            self.current_character = None
            self.current_group = None
            self.update_listbox()

    def edit_party_members(self):
        if not self.current_party:
            messagebox.showwarning("경고", "편집할 파티를 선택하세요!")
            return
        all_chars = []
        for g in ["1군","2군","3군","4군"]:
            all_chars.extend(list(self.tasks[g].keys()))
        top = tk.Toplevel(self.root)
        top.title(f"{self.current_party} 멤버 편집")
        vars = {}
        for i, c in enumerate(all_chars):
            var = tk.BooleanVar(value=(c in self.parties[self.current_party]))
            chk = tk.Checkbutton(top, text=c, variable=var)
            chk.grid(row=i//4, column=i%4, sticky="w")
            vars[c] = var
        def save():
            self.parties[self.current_party] = [c for c,v in vars.items() if v.get()]
            self.save_data()
            top.destroy()
            self.update_listbox()
        tk.Button(top, text="확인", command=save).grid(row=(len(all_chars)//4)+1, column=0, columnspan=4)

    # --- 숙제 관리 ---
    def add_task(self):
        task = self.task_entry.get()
        if not task: return
        if self.current_character:
            self.tasks[self.current_group][self.current_character].append({"task": task,"done":False,"comment":""})
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]:
                        self.tasks[g][char].append({"task": task,"done":False,"comment":""})
        self.task_entry.delete(0, tk.END)
        self.update_listbox()
        self.save_data()

    def update_listbox(self):
        self.task_listbox.delete(0, tk.END)
        keyword = self.filter_entry.get().strip().lower()
        entries = []

        # 데이터 수집
        if self.current_character:
            entries = [(self.current_group, self.current_character, t) for t in self.tasks[self.current_group][self.current_character]]
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]:
                        entries.extend([(g,char,t) for t in self.tasks[g][char]])

        # 리스트박스 표시
        for i,(g,char,t) in enumerate(entries,start=1):
            if keyword and keyword not in t["task"].lower():
                continue
            status = "✅" if t["done"] else "❌"
            comment = f" (메모: {t['comment']})" if t["comment"] else ""
            self.task_listbox.insert(tk.END,f"{i}. [{char}] {t['task']} {status}{comment}")
            self.task_listbox.itemconfig(tk.END, {'bg': GROUP_COLORS.get(g,'white')})

    def apply_filter(self): self.update_listbox()
    def mark_done(self):
        try: selection=self.task_listbox.curselection()[0]; task=self._get_task_by_index(selection); task["done"]=not task["done"]; self.update_listbox(); self.save_data()
        except: messagebox.showwarning("경고","숙제를 선택하세요!")
    def add_comment(self):
        try: selection=self.task_listbox.curselection()[0]; task=self._get_task_by_index(selection); comment=simpledialog.askstring("코멘트","메모를 입력하세요:",initialvalue=task["comment"]); task["comment"]=comment if comment is not None else task["comment"]; self.update_listbox(); self.save_data()
        except: messagebox.showwarning("경고","숙제를 선택하세요!")
    def delete_task(self):
        try: selection=self.task_listbox.curselection()[0]; task=self._get_task_by_index(selection); self._remove_task(task); self.update_listbox(); self.save_data()
        except: messagebox.showwarning("경고","삭제할 숙제를 선택하세요!")
    def toggle_all_tasks(self):
        tasks=[]
        if self.current_character: tasks=self.tasks[self.current_group][self.current_character]
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]: tasks.extend(self.tasks[g][char])
        if not tasks: return
        all_done = all(t["done"] for t in tasks)
        for t in tasks: t["done"]=not all_done
        self.update_listbox()
        self.save_data()

    # --- 헬퍼 ---
    def _get_task_by_index(self,index):
        keyword=self.filter_entry.get().strip().lower()
        count=-1
        entries=[]
        if self.current_character:
            entries=[t for t in self.tasks[self.current_group][self.current_character]]
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]: entries.extend(self.tasks[g][char])
        for t in entries:
            if keyword and keyword not in t["task"].lower(): continue
            count+=1
            if count==index: return t
    def _remove_task(self,task_to_remove):
        for g in ["1군","2군","3군","4군"]:
            for char in self.tasks[g]:
                if task_to_remove in self.tasks[g][char]: self.tasks[g][char].remove(task_to_remove)
        for char in self.tasks["공통"]:
            if task_to_remove in self.tasks["공통"][char]: self.tasks["공통"][char].remove(task_to_remove)

    # --- 저장/불러오기 ---
    def save_data(self):
        try:
            with open(SAVE_FILE,"w",encoding="utf-8") as f: json.dump({"tasks":self.tasks,"parties":self.parties},f,ensure_ascii=False,indent=2)
        except Exception as e: messagebox.showerror("에러",f"저장 실패: {e}")
    def load_data(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE,"r",encoding="utf-8") as f:
                    data=json.load(f)
                    self.tasks=data.get("tasks",self.tasks)
                    self.parties=data.get("parties",{})
            except: messagebox.showwarning("경고","저장된 데이터를 불러올 수 없습니다.")
    def on_close(self): self.save_data(); self.root.destroy()

# --- 실행 ---
if __name__=="__main__":
    root=tk.Tk()
    app=TaskManager(root)
    root.mainloop()
