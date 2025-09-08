import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json, os, sys

# 저장 파일 위치
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "tasks.json")

# 군별 색상
GROUP_COLORS = {
    "공통": "#D3D3D3",
    "1군": "#40E0D0",   # 태초색 (에메랄드)
    "2군": "#FFFF66",   # 에픽 노랑
    "3군": "#FFA500",   # 레전드 주황
    "4군": "#FF69B4"    # 유니크 핑크
}

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("던파 숙제 스케줄러 + 벞교 파티")
        self.root.geometry("1050x1000")

        # 데이터 초기화
        self.tasks = {"공통":{"공통":[]}, "1군":{}, "2군":{}, "3군":{}, "4군":{}}
        self.parties = {}
        self.load_data()

        self.current_group = None
        self.current_character = None
        self.current_party = None

        # --- UI ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)
        self.char_selectors = {}
        for group in ["공통","1군","2군","3군","4군"]:
            frame = tk.LabelFrame(top_frame, text=group, padx=5, pady=5)
            frame.pack(side=tk.LEFT, padx=5)
            if group == "공통":
                self.char_selectors[group] = ttk.Combobox(frame, values=["공통"], state="readonly", width=10)
                self.char_selectors[group].set("공통")
                self.char_selectors[group].pack()
            else:
                self.char_selectors[group] = ttk.Combobox(frame, values=list(self.tasks[group].keys()), state="readonly", width=10)
                self.char_selectors[group].pack()
                tk.Button(frame, text="캐릭터 추가", command=lambda g=group: self.add_character(g)).pack(pady=2)
            self.char_selectors[group].bind("<<ComboboxSelected>>", lambda e,g=group: self.switch_character(g))

        # 벞교 파티
        party_frame = tk.LabelFrame(root, text="벞교 파티", padx=10, pady=5)
        party_frame.pack(pady=5)
        self.party_selector = ttk.Combobox(party_frame, values=list(self.parties.keys()), state="readonly", width=30)
        self.party_selector.pack(side=tk.LEFT, padx=5)
        self.party_selector.bind("<<ComboboxSelected>>", lambda e: self.switch_party())
        tk.Button(party_frame, text="파티 추가", command=self.add_party).pack(side=tk.LEFT, padx=5)
        tk.Button(party_frame, text="파티 편집", command=self.edit_party_members).pack(side=tk.LEFT, padx=5)

        # 검색/필터
        filter_frame = tk.Frame(root)
        filter_frame.pack(pady=5)
        tk.Label(filter_frame, text="검색:").pack(side=tk.LEFT)
        self.filter_entry = tk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="적용", command=self.update_treeview).pack(side=tk.LEFT)
        tk.Button(filter_frame, text="초기화", command=lambda: (self.filter_entry.delete(0,tk.END), self.update_treeview())).pack(side=tk.LEFT, padx=5)

        # 범례
        legend_frame = tk.Frame(root)
        legend_frame.pack(pady=5)
        for g,color in GROUP_COLORS.items():
            tk.Label(legend_frame, text=g, bg=color, width=10).pack(side=tk.LEFT, padx=3)
        tk.Label(legend_frame, text="완료=✔(형광)", fg="green").pack(side=tk.LEFT, padx=3)
        tk.Label(legend_frame, text="미완료=✘(빨강)", fg="red").pack(side=tk.LEFT, padx=3)

        # Treeview
        columns=("task","status")
        self.tree=ttk.Treeview(root, columns=columns, show="headings", height=20)
        self.tree.heading("task", text="숙제")
        self.tree.heading("status", text="상태")
        self.tree.column("task", width=750)
        self.tree.column("status", width=100, anchor="center")
        self.tree.pack(pady=5, fill=tk.X)
        self.tree.bind("<Button-1>", self.on_tree_click)

        # 스타일 변경 (✔ 형광, ✘ 빨강)
        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=("맑은 고딕", 11))
        style.map("Treeview")

        # 숙제 추가
        entry_frame=tk.Frame(root)
        entry_frame.pack()
        self.task_entry=tk.Entry(entry_frame, width=60)
        self.task_entry.grid(row=0,column=0,padx=5)
        tk.Button(entry_frame,text="숙제 추가",command=self.add_task).grid(row=0,column=1)

        # 버튼
        button_frame=tk.Frame(root)
        button_frame.pack(pady=5)
        tk.Button(button_frame,text="코멘트 추가/보기",command=self.add_comment).grid(row=0,column=0,padx=5)
        tk.Button(button_frame,text="숙제 삭제",command=self.delete_task).grid(row=0,column=1,padx=5)
        tk.Button(button_frame,text="전체 완료/해제",command=self.toggle_all_tasks).grid(row=0,column=2,padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.switch_character("공통")

    # ---------------- 캐릭터 & 파티 ----------------
    def add_character(self, group):
        name = simpledialog.askstring("캐릭터 추가", f"{group}에 추가할 캐릭터 이름:")
        if name and name not in self.tasks[group]:
            self.tasks[group][name]=[]
            self.char_selectors[group]["values"]=list(self.tasks[group].keys())
            self.char_selectors[group].set(name)
            self.switch_character(group)
            self.save_data()

    def switch_character(self, group):
        self.current_group=group
        self.current_character=self.char_selectors[group].get()
        self.current_party=None
        self.party_selector.set('')
        self.update_treeview()

    def add_party(self):
        name=simpledialog.askstring("파티 추가","파티 이름:")
        if not name: return
        members=simpledialog.askstring("파티 구성","캐릭터 이름 ','로 구분:")
        if members: self.parties[name]=[m.strip() for m in members.split(",")]
        self.party_selector["values"]=list(self.parties.keys())
        self.party_selector.set(name)
        self.switch_party()
        self.save_data()

    def switch_party(self):
        party=self.party_selector.get()
        if party in self.parties:
            self.current_party=party
            self.current_character=None
            self.current_group=None
            self.update_treeview()

    def edit_party_members(self):
        if not self.current_party:
            messagebox.showwarning("경고","파티를 선택하세요!")
            return
        all_chars=[]
        for g in ["1군","2군","3군","4군"]:
            all_chars.extend(list(self.tasks[g].keys()))
        top=tk.Toplevel(self.root)
        top.title(f"{self.current_party} 편집")
        vars={}
        for i,c in enumerate(all_chars):
            var=tk.BooleanVar(value=(c in self.parties[self.current_party]))
            tk.Checkbutton(top,text=c,variable=var).grid(row=i//4,column=i%4,sticky="w")
            vars[c]=var
        def save():
            self.parties[self.current_party]=[c for c,v in vars.items() if v.get()]
            self.save_data()
            top.destroy()
            self.update_treeview()
        tk.Button(top,text="확인",command=save).grid(row=(len(all_chars)//4)+1,column=0,columnspan=4)

    # ---------------- 숙제 ----------------
    def add_task(self):
        task=self.task_entry.get()
        if not task: return
        if self.current_character:
            self.tasks[self.current_group][self.current_character].append({"task":task,"done":False,"comment":""})
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]:
                        self.tasks[g][char].append({"task":task,"done":False,"comment":""})
        self.task_entry.delete(0,tk.END)
        self.update_treeview()
        self.save_data()

    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        keyword=self.filter_entry.get().strip().lower()
        entries=[]
        if self.current_character:
            entries=[(self.current_group,self.current_character,t) for t in self.tasks[self.current_group][self.current_character]]
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]:
                        entries.extend([(g,char,t) for t in self.tasks[g][char]])
        for g,char,t in entries:
            if keyword and keyword not in t["task"].lower(): continue
            if t["done"]:
                status="✔"
                tags=(g,"done")
            else:
                status="✘"
                tags=(g,"notdone")
            iid=self.tree.insert("", "end", values=(f"[{char}] {t['task']}", status), tags=tags)
            # 군별 색
            self.tree.tag_configure(g, background=GROUP_COLORS[g])
            # 완료 색 (형광), 미완료 색 (빨강)
            self.tree.tag_configure("done", foreground="green")
            self.tree.tag_configure("notdone", foreground="red")

    # ---------------- Treeview 클릭 (완료 토글) ----------------
    def on_tree_click(self,event):
        region=self.tree.identify_region(event.x,event.y)
        if region!="cell": return
        col=self.tree.identify_column(event.x)
        if col!="#2": return  # 상태 컬럼만
        iid=self.tree.identify_row(event.y)
        if not iid: return
        item=self.tree.item(iid)
        text=item["values"][0]
        char=text[1:text.index("]")]
        task_text=text[text.index("]")+2:]
        for g in ["공통","1군","2군","3군","4군"]:
            if char in self.tasks[g]:
                for t in self.tasks[g][char]:
                    if t["task"]==task_text:
                        t["done"]=not t["done"]
        self.update_treeview()
        self.save_data()

    # ---------------- 기타 기능 ----------------
    def get_selected_task(self):
        sel=self.tree.selection()
        if not sel: return None,None,None
        item=self.tree.item(sel[0])
        text=item["values"][0]
        char=text[1:text.index("]")]
        task_text=text[text.index("]")+2:]
        for g in ["공통","1군","2군","3군","4군"]:
            if char in self.tasks[g]:
                for t in self.tasks[g][char]:
                    if t["task"]==task_text:
                        return g,char,t
        return None,None,None

    def add_comment(self):
        g,char,t=self.get_selected_task()
        if not t: return
        comment=simpledialog.askstring("코멘트", "코멘트 입력:", initialvalue=t.get("comment",""))
        if comment is not None:
            t["comment"]=comment
            self.save_data()

    def delete_task(self):
        g,char,t=self.get_selected_task()
        if not t: return
        self.tasks[g][char].remove(t)
        self.update_treeview()
        self.save_data()

    def toggle_all_tasks(self):
        all_done=True
        entries=[]
        if self.current_character:
            entries=[t for t in self.tasks[self.current_group][self.current_character]]
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]: entries.extend(self.tasks[g][char])
        for t in entries:
            if not t["done"]: all_done=False
        new_state=not all_done
        for t in entries: t["done"]=new_state
        self.update_treeview()
        self.save_data()

    # ---------------- 저장/불러오기 ----------------
    def save_data(self):
        try:
            with open(SAVE_FILE,"w",encoding="utf-8") as f:
                json.dump({"tasks":self.tasks,"parties":self.parties},f,ensure_ascii=False,indent=2)
        except Exception as e:
            messagebox.showerror("에러",f"저장 실패: {e}")

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE,"r",encoding="utf-8") as f:
                    data=json.load(f)
                    self.tasks=data.get("tasks",self.tasks)
                    self.parties=data.get("parties",{})
            except: messagebox.showwarning("경고","저장된 데이터를 불러올 수 없습니다.")

    def on_close(self):
        self.save_data()
        self.root.destroy()

# ---------------- 실행 ----------------
if __name__=="__main__":
    root=tk.Tk()
    app=TaskManager(root)
    root.mainloop()
