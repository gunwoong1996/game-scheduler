import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os
import sys

# 저장 파일 위치
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "tasks.json")

# 군별 색상
GROUP_COLORS = {
    "공통": "#B8B4B4",
    "1군": "#0FE2CD",   # 태초색(에메랄드)
    "2군": "#FFFF66",   # 에픽 노랑
    "3군": "#FFA500",   # 레전더리 오렌지
    "4군": "#FF69B4"    # 유니크 핑크
}
DONE_COLOR = "#129C05"     # 완료 연두(덜 쨍하게)
UNDONE_COLOR = "#B30707"   # 미완료 빨강

# 숙제 종류
CATEGORIES = ["일일", "주간", "월간"]
FILTER_CATEGORIES = ["전체"] + CATEGORIES

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("던파 숙제 스케줄러")
        self.root.geometry("1000x950") #창 크기

        # 데이터 초기화
        # tasks[group][character] = [ {task, done, comment, cat}, ... ]
        self.tasks = {"공통":{"공통":[]}, "1군":{}, "2군":{}, "3군":{}, "4군":{}}
        self.parties = {}
        self.load_data()

        self.current_group = None
        self.current_character = None
        self.current_party = None

        # --- UI ---

        # 상단: 군/캐릭터 선택
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5)
        self.char_selectors = {}
        for group in ["공통","1군","2군","3군","4군"]:
            frame = tk.LabelFrame(top_frame, text=group, padx=3, pady=5, bg=GROUP_COLORS[group])
            frame.pack(side=tk.LEFT, padx=5)
            if group == "공통":
                self.char_selectors[group] = ttk.Combobox(frame, values=["공통"], state="readonly", width=12)
                self.char_selectors[group].set("공통")
                self.char_selectors[group].pack()
            else:
                self.char_selectors[group] = ttk.Combobox(frame, values=list(self.tasks[group].keys()), state="readonly", width=12)
                self.char_selectors[group].pack()
                tk.Button(frame, text="캐릭터 추가", command=lambda g=group: self.add_character(g)).pack(pady=2)
            self.char_selectors[group].bind("<<ComboboxSelected>>", lambda e,g=group: self.switch_character(g))

        # 벞교 파티
        party_frame = tk.LabelFrame(root, text="벞교 파티", padx=10, pady=5)
        party_frame.pack(pady=5, fill=tk.X)
        self.party_selector = ttk.Combobox(party_frame, values=list(self.parties.keys()), state="readonly", width=30)
        self.party_selector.pack(side=tk.LEFT, padx=5)
        self.party_selector.bind("<<ComboboxSelected>>", lambda e: self.switch_party())
        tk.Button(party_frame, text="파티 추가", command=self.add_party).pack(side=tk.LEFT, padx=5)
        tk.Button(party_frame, text="파티 편집", command=self.edit_party_members).pack(side=tk.LEFT, padx=5)

        # 검색/필터 (종류 필터 추가)
        filter_frame = tk.Frame(root)
        filter_frame.pack(pady=5, fill=tk.X)
        tk.Label(filter_frame, text="검색:").pack(side=tk.LEFT)
        self.filter_entry = tk.Entry(filter_frame, width=30)
        self.filter_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(filter_frame, text="종류:").pack(side=tk.LEFT, padx=(10,2))
        self.cat_filter = ttk.Combobox(filter_frame, values=FILTER_CATEGORIES, state="readonly", width=8)
        self.cat_filter.set("전체")
        self.cat_filter.pack(side=tk.LEFT)
        self.cat_filter.bind("<<ComboboxSelected>>", lambda e: self.update_treeview())

        tk.Button(filter_frame, text="적용", command=self.update_treeview).pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="초기화", command=self.reset_filter).pack(side=tk.LEFT, padx=5)

        # 범례 표시
        legend_frame = tk.Frame(root)
        legend_frame.pack(pady=5)
        for g,color in GROUP_COLORS.items():
            tk.Label(legend_frame, text=g, bg=color, width=10).pack(side=tk.LEFT, padx=3)

        # Treeview (종류 컬럼 추가)
        columns=("cat","task","status","comment")
        self.tree=ttk.Treeview(root, columns=columns, show="headings", height=24)
        self.tree.heading("cat", text="종류")
        self.tree.heading("task", text="숙제")
        self.tree.heading("status", text="상태")
        self.tree.heading("comment", text="코멘트")

        self.tree.column("cat", width=80, anchor="center")
        self.tree.column("task", width=630)
        self.tree.column("status", width=80, anchor="center")
        self.tree.column("comment", width=300)
        self.tree.pack(pady=5, fill=tk.BOTH, expand=True)

        # Treeview 클릭 (상태 토글)
        self.tree.bind("<Button-1>", self.on_tree_click)

        # --- 선택/호버 오버레이 억제 (행 배경 유지) ---
        style = ttk.Style()

        try:
            style.theme_use("clam")  # 선택/배경 매핑 제어가 잘 되는 테마
        except:
            pass

        style.configure(
            "Treeview",
            font=("맑은 고딕", 10, "bold"),
            rowheight=24,
            borderwidth=0,
            relief="flat"
        )
        
        #style.map("Treeview", background=[("selected", "white")], foreground=[("selected", "black")]) 
      

        self.tree.bind("<Button-1>", self.on_tree_click)

        # 숙제 추가
        entry_frame=tk.Frame(root)
        entry_frame.pack(pady=5)
        self.task_entry=tk.Entry(entry_frame, width=70)
        self.task_entry.grid(row=0,column=0,padx=5)

        tk.Label(entry_frame, text="종류:").grid(row=0, column=1, padx=(8,2))
        self.cat_add = ttk.Combobox(entry_frame, values=CATEGORIES, state="readonly", width=8)
        self.cat_add.set("일일")
        self.cat_add.grid(row=0, column=2)

        tk.Button(entry_frame,text="숙제 추가",command=self.add_task).grid(row=0,column=3, padx=8)

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
        name = simpledialog.askstring("캐릭터 추가", f"{group}에 추가할 캐릭터 이름(직업명 포함 추천):")
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
        all_chars = sorted(set(all_chars))
        top=tk.Toplevel(self.root)
        top.title(f"{self.current_party} 편집")
        vars={}
        for i,c in enumerate(all_chars):
            var=tk.BooleanVar(value=(c in self.parties[self.current_party]))
            tk.Checkbutton(top,text=c,variable=var).grid(row=i//3,column=i%3,sticky="w", padx=6, pady=2)
            vars[c]=var
        def save():
            self.parties[self.current_party]=[c for c,v in vars.items() if v.get()]
            self.save_data()
            top.destroy()
            self.update_treeview()
        tk.Button(top,text="확인",command=save).grid(row=(len(all_chars)//3)+1,column=0,columnspan=3, pady=6)

    # ---------------- 숙제 ----------------
    def add_task(self):
        task=self.task_entry.get().strip()
        cat = self.cat_add.get()
        if not task: return
        new_item = {"task":task,"done":False,"comment":"", "cat":cat}
        if self.current_character:
            self.tasks[self.current_group][self.current_character].append(new_item)
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]:
                        self.tasks[g][char].append(new_item.copy())
        self.task_entry.delete(0,tk.END)
        self.update_treeview()
        self.save_data()

    def update_treeview(self):
        self.tree.delete(*self.tree.get_children())
        keyword=self.filter_entry.get().strip().lower()
        cat_filter = self.cat_filter.get()  # 전체/일일/주간/월간

        entries=[]
        if self.current_character:
            entries=[(self.current_group,self.current_character,t) for t in self.tasks[self.current_group][self.current_character]]
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]:
                        entries.extend([(g,char,t) for t in self.tasks[g][char]])

        for g,char,t in entries:
            # 종류 필터
            if cat_filter != "전체" and t.get("cat") != cat_filter:
                continue
            # 검색 필터
            text_all = f"{t.get('task','')} {t.get('comment','')}".lower()
            if keyword and keyword not in text_all:
                continue

            status="✔" if t.get("done") else "✘"
            # 행 추가 (종류/숙제/상태/코멘트)
            iid=self.tree.insert("", "end",
                                 values=(t.get("cat",""), f"[{char}] {t.get('task','')}", status, t.get("comment","")),
                                 tags=(g,))
            # 군별 배경
            self.tree.tag_configure(g, background=GROUP_COLORS[g], font=("맑은 고딕", 10, "bold"))
            # 상태 색상(행 전경색) - Treeview 한계상 행 전체 전경색이 바뀌지만 ✔/✘이 가장 눈에 띔
            if t.get("done"):
                self.tree.tag_configure(f"{iid}_done", foreground=DONE_COLOR)
                self.tree.item(iid, tags=(g, f"{iid}_done"))
            else:
                self.tree.tag_configure(f"{iid}_undone", foreground=UNDONE_COLOR)
                self.tree.item(iid, tags=(g, f"{iid}_undone"))

    # 상태 토글 (상태 컬럼만)
    def on_tree_click(self,event):
        region=self.tree.identify_region(event.x,event.y)
        if region!="cell": return
        col=self.tree.identify_column(event.x)
        if col!="#3": return  # 상태 컬럼만
        iid=self.tree.identify_row(event.y)
        if not iid: return
        item=self.tree.item(iid)
        cat_val, taskcol, _status, _comment = item["values"]
        # taskcol은 "[캐릭] 내용"
        try:
            char = taskcol[1:taskcol.index("]")]
            task_text = taskcol[taskcol.index("]")+2:]
        except:
            return
        # 위치 찾기 & 토글
        for g in ["공통","1군","2군","3군","4군"]:
            if self.current_party:
                # 파티 보기일 때는 모든 군 체크
                if char in self.tasks[g]:
                    for t in self.tasks[g][char]:
                        if t.get("task")==task_text and t.get("cat","")==cat_val:
                            t["done"]=not t.get("done",False)
                            break
            else:
                # 캐릭터 보기일 때는 현재 군만
                if self.current_group==g and char in self.tasks[g]:
                    for t in self.tasks[g][char]:
                        if t.get("task")==task_text and t.get("cat","")==cat_val:
                            t["done"]=not t.get("done",False)
                            break
        self.update_treeview()
        self.save_data()

    # 선택 헬퍼
    def get_selected_task(self):
        sel=self.tree.selection()
        if not sel: return None,None,None,None
        item=self.tree.item(sel[0])
        cat_val, taskcol, _status, _comment = item["values"]
        try:
            char = taskcol[1:taskcol.index("]")]
            task_text = taskcol[taskcol.index("]")+2:]
        except:
            return None,None,None,None
        for g in ["공통","1군","2군","3군","4군"]:
            if char in self.tasks[g]:
                for t in self.tasks[g][char]:
                    if t.get("task")==task_text and t.get("cat","")==cat_val:
                        return g,char,t,cat_val
        return None,None,None,None

    # 코멘트/삭제/전체완료
    def add_comment(self):
        g,char,t,_cat = self.get_selected_task()
        if not t: 
            messagebox.showinfo("알림","코멘트를 추가할 숙제를 선택하세요.")
            return
        comment=simpledialog.askstring("코멘트", "코멘트 입력:", initialvalue=t.get("comment",""))
        if comment is not None:
            t["comment"]=comment
            self.save_data()
            self.update_treeview()

    def delete_task(self):
        g,char,t,_cat = self.get_selected_task()
        if not t: 
            messagebox.showinfo("알림","삭제할 숙제를 선택하세요.")
            return
        self.tasks[g][char].remove(t)
        self.update_treeview()
        self.save_data()

    def toggle_all_tasks(self):
        entries=[]
        if self.current_character:
            entries=[t for t in self.tasks[self.current_group][self.current_character]]
        elif self.current_party:
            for char in self.parties[self.current_party]:
                for g in ["1군","2군","3군","4군"]:
                    if char in self.tasks[g]: entries.extend(self.tasks[g][char])
        # 종류 필터 적용(현재 화면 기준)
        cat_filter = self.cat_filter.get()
        if cat_filter != "전체":
            entries = [t for t in entries if t.get("cat")==cat_filter]

        if not entries: return
        all_done = all(t.get("done") for t in entries)
        new_state = not all_done
        for t in entries: t["done"]=new_state
        self.update_treeview()
        self.save_data()

    # 저장/불러오기
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
                    # cat 필드가 없던 예전 데이터 보정
                    for g in self.tasks:
                        for ch in self.tasks[g]:
                            for t in self.tasks[g][ch]:
                                if "cat" not in t:
                                    t["cat"]="일일"  # 기본값
                    self.parties=data.get("parties",{})
            except:
                messagebox.showwarning("경고","저장된 데이터를 불러올 수 없습니다.")

    def reset_filter(self):
        self.filter_entry.delete(0, tk.END)
        self.cat_filter.set("전체")
        self.update_treeview()

    def on_close(self):
        self.save_data()
        self.root.destroy()

# ---------------- 실행 ----------------
if __name__=="__main__":
    root=tk.Tk()
    app=TaskManager(root)
    root.mainloop()
