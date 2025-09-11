import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json, os, sys

# ================== 경로/저장 ==================
BASE_DIR  = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(BASE_DIR, "tasks.json")

# ================== 색상/상수 ==================
GROUP_COLORS = {
    "공통":"#B8B4B4",
    "1군":"#0FE2CD",   # 태초(에메랄드)
    "2군":"#FFFF66",   # 에픽 노랑
    "3군":"#FFA500",   # 레전더리 주황
    "4군":"#FF69B4",   # 유니크 핑크
}
DONE_COLOR   = "#129C05"   # 완료(연두)
UNDONE_COLOR = "#B30707"   # 미완료(빨강)

CATEGORIES        = ["일일","주간","월간"]
FILTER_CATEGORIES = ["전체"] + CATEGORIES
BUFF_TAGS         = ["나벨","상던","베누스","이내"]  # 네 개 모두 포함

# 보드뷰 카드/배치
CARD_W, CARD_H    = 200, 100
BOARD_X_STEP      = 220
BOARD_Y_STEP      = 120
COLS              = 4
GROUP_GAP_Y       = 24

class TaskManager:
    def __init__(self, root):
        self.root = root
        self.root.title("던파 숙제 스케줄러")
        self.root.geometry("1200x960")

        # 데이터 구조
        # tasks[group][character] = [ {task, done, comment, cat}, ... ]
        self.tasks   = {"공통":{"공통":[]}, "1군":{}, "2군":{}, "3군":{}, "4군":{}}
        self.parties = {}
        self.buff_select = {}    # {캐릭명: set(태그)}
        self.adhoc_party = []    # 즉흥 파티 멤버(세션 전용, 저장 안 함)

        self.load_data()

        self.current_group     = None
        self.current_character = None
        self.current_party     = None

        # =============== 상단: 군/캐릭터 선택 ===============
        top = tk.Frame(root); top.pack(pady=5)
        self.char_selectors = {}
        for g in ["공통","1군","2군","3군","4군"]:
            f = tk.LabelFrame(top, text=g, bg=GROUP_COLORS[g], padx=6, pady=6); f.pack(side=tk.LEFT, padx=5)
            if g == "공통":
                cb = ttk.Combobox(f, values=["공통"], state="readonly", width=12)
                cb.set("공통"); cb.pack()
                self.char_selectors[g] = cb
            else:
                cb = ttk.Combobox(f, values=list(self.tasks[g].keys()), state="readonly", width=12); cb.pack()
                row = tk.Frame(f, bg=GROUP_COLORS[g]); row.pack(pady=4)
                tk.Button(row, text="추가", command=lambda gr=g: self.add_character(gr)).pack(side=tk.LEFT, padx=2)
                tk.Button(row, text="삭제", command=lambda gr=g: self.delete_character(gr)).pack(side=tk.LEFT, padx=2)
                tk.Button(row, text="이동", command=lambda gr=g: self.move_character(gr)).pack(side=tk.LEFT, padx=2)
                self.char_selectors[g] = cb
            cb.bind("<<ComboboxSelected>>", lambda e, gr=g: self.switch_character(gr))

        # =============== 파티 ===============
        pf = tk.LabelFrame(root, text="벞교 파티", padx=8, pady=6); pf.pack(fill=tk.X, pady=5)
        self.party_selector = ttk.Combobox(pf, values=list(self.parties.keys()), state="readonly", width=30)
        self.party_selector.pack(side=tk.LEFT, padx=5)
        self.party_selector.bind("<<ComboboxSelected>>", lambda e: self.switch_party())
        tk.Button(pf, text="추가", command=self.add_party).pack(side=tk.LEFT, padx=5)
        tk.Button(pf, text="편집", command=self.edit_party).pack(side=tk.LEFT, padx=5)
        tk.Button(pf, text="삭제", command=self.delete_party).pack(side=tk.LEFT, padx=5)

        # =============== 검색/종류 필터 ===============
        ff = tk.Frame(root); ff.pack(fill=tk.X, pady=5)
        tk.Label(ff, text="검색:").pack(side=tk.LEFT)
        self.filter_entry = tk.Entry(ff, width=30); self.filter_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(ff, text="종류:").pack(side=tk.LEFT, padx=(10,2))
        self.cat_filter = ttk.Combobox(ff, values=FILTER_CATEGORIES, state="readonly", width=8)
        self.cat_filter.set("전체"); self.cat_filter.pack(side=tk.LEFT)
        self.cat_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_views())
        tk.Button(ff, text="적용", command=self.refresh_views).pack(side=tk.LEFT, padx=5)
        tk.Button(ff, text="초기화", command=self.reset_filter).pack(side=tk.LEFT, padx=5)

        # =============== Notebook ===============
        self.nb = ttk.Notebook(root); self.nb.pack(fill=tk.BOTH, expand=True)
        self.list_tab  = tk.Frame(self.nb)
        self.board_tab = tk.Frame(self.nb)
        self.nb.add(self.list_tab,  text="리스트 뷰")
        self.nb.add(self.board_tab, text="보드 뷰")
        self.nb.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # =============== 리스트 뷰 ===============
        cols = ("cat","task","status","comment")
        self.tree = ttk.Treeview(self.list_tab, columns=cols, show="headings", height=24)
        for c in cols: self.tree.heading(c, text=c)
        self.tree.column("cat", width=60, anchor="center")
        self.tree.column("task", width=700)
        self.tree.column("status", width=60, anchor="center")
        self.tree.column("comment", width=300)
        self.tree.pack(fill=tk.BOTH, expand=True, pady=5)
        self.tree.bind("<Button-1>", self.on_tree_click)

        # Treeview 스타일: 선택 하이라이트 제거 + 굵은 글씨
        style = ttk.Style()
        try: style.theme_use("clam")
        except: pass
        style.configure("Treeview", font=("맑은 고딕",10,"bold"), rowheight=24, borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected","")], foreground=[("selected","")])

        # =============== 보드 뷰 상단 ===============
        bt = tk.Frame(self.board_tab); bt.pack(fill=tk.X, pady=(5,0))
        # 태그 전용 보기(필터) 4개
        self.buff_filters_vars = {k: tk.BooleanVar(value=False) for k in BUFF_TAGS}
        for tag in BUFF_TAGS:
            tk.Checkbutton(bt, text=f"{tag} 보기", variable=self.buff_filters_vars[tag],
                           command=self.render_board).pack(side=tk.LEFT, padx=6)

        # 즉흥 파티 버튼
        tk.Button(bt, text="즉흥 파티 보기", command=self.show_adhoc_party).pack(side=tk.LEFT, padx=10)
        tk.Button(bt, text="즉흥 파티 초기화", command=self.clear_adhoc_party).pack(side=tk.LEFT, padx=5)

        # Canvas + Scrollbar
        canvas_frame = tk.Frame(self.board_tab); canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(canvas_frame, bg="#F5F5F5", highlightthickness=0)
        self.scroll_y = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.canvas.pack(side="left", fill=tk.BOTH, expand=True)
        self.scroll_y.pack(side="right", fill="y")
        # 마우스 휠 스크롤(Windows/Mac/Linux)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>",  self._on_mousewheel)
        self.canvas.bind_all("<Button-5>",  self._on_mousewheel)

        # =============== 숙제 입력/버튼 ===============
        ef = tk.Frame(root); ef.pack(pady=5)
        self.task_entry = tk.Entry(ef, width=70); self.task_entry.grid(row=0, column=0, padx=5)
        self.cat_add = ttk.Combobox(ef, values=CATEGORIES, state="readonly", width=8)
        self.cat_add.set("일일"); self.cat_add.grid(row=0, column=1, padx=5)
        tk.Button(ef, text="숙제 추가", command=self.add_task).grid(row=0, column=2, padx=8)

        bf = tk.Frame(root); bf.pack(pady=5)
        tk.Button(bf, text="코멘트", command=self.add_comment).pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="숙제 삭제", command=self.delete_task).pack(side=tk.LEFT, padx=5)
        tk.Button(bf, text="전체 완료/해제", command=self.toggle_all).pack(side=tk.LEFT, padx=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        # 기본 선택
        self.switch_character("공통")

    # ================= 공통 갱신 =================
    def refresh_views(self):
        self.update_tree()
        if self.nb.tab(self.nb.select(), "text") == "보드 뷰":
            self.render_board()

    def on_tab_changed(self, event):
        if self.nb.tab(self.nb.select(), "text") == "보드 뷰":
            self.render_board()

    # ================= 리스트 뷰 =================
    def update_tree(self):
        self.tree.delete(*self.tree.get_children())
        kw   = self.filter_entry.get().strip().lower()
        catf = self.cat_filter.get()

        entries = []
        if self.current_character:
            entries = [(self.current_group, self.current_character, t) for t in self.tasks[self.current_group][self.current_character]]
        elif self.current_party:
            for ch in self.parties.get(self.current_party, []):
                for g in ["1군","2군","3군","4군"]:
                    if ch in self.tasks[g]:
                        entries.extend([(g, ch, t) for t in self.tasks[g][ch]])

        for g, ch, t in entries:
            if catf != "전체" and t.get("cat") != catf: continue
            if kw and kw not in (t.get("task","") + t.get("comment","")).lower(): continue
            status = "✔" if t.get("done") else "✘"
            iid = self.tree.insert("", "end", values=(t.get("cat",""), f"[{ch}] {t.get('task','')}", status, t.get("comment","")), tags=(g,))
            # 군별 배경 + 상태 전경색
            self.tree.tag_configure(g, background=GROUP_COLORS[g])
            self.tree.tag_configure(f"{iid}_{'d' if t.get('done') else 'u'}",
                                    foreground=(DONE_COLOR if t.get("done") else UNDONE_COLOR))
            self.tree.item(iid, tags=(g, f"{iid}_{'d' if t.get('done') else 'u'}"))

    def on_tree_click(self, e):
        # 상태 컬럼(#3)에서만 토글
        if self.tree.identify_column(e.x) != "#3": return
        iid = self.tree.identify_row(e.y)
        if not iid: return
        cat, taskcol, _, _ = self.tree.item(iid)["values"]
        try:
            ch  = taskcol[1:taskcol.index("]")]
            txt = taskcol[taskcol.index("]")+2:]
        except: 
            return
        for g in self.tasks:
            if self.current_party:
                if ch in self.tasks[g]:
                    for t in self.tasks[g][ch]:
                        if t.get("task")==txt and t.get("cat")==cat:
                            t["done"] = not t.get("done", False); break
            else:
                if self.current_group == g and ch in self.tasks[g]:
                    for t in self.tasks[g][ch]:
                        if t.get("task")==txt and t.get("cat")==cat:
                            t["done"] = not t.get("done", False); break
        self.save(); self.refresh_views()

    # ================= 보드 뷰 =================
    def render_board(self, only_adhoc=False):
        self.canvas.delete("all")
        kw   = self.filter_entry.get().strip().lower()
        catf = self.cat_filter.get()
        active_filters = [tag for tag, var in self.buff_filters_vars.items() if var.get()]
        y_offset = 20

        # --- 즉흥 파티 전용 보기 (4인 단위 묶기) ---
        if only_adhoc:
            if not self.adhoc_party:
                self.canvas.create_text(20,20,text="즉흥 파티가 비어있습니다.", anchor="nw", font=("맑은 고딕",11,"bold"))
                return
            party_count = (len(self.adhoc_party) + 3) // 4
            for p in range(party_count):
                self.canvas.create_text(12, y_offset, text=f"■ 즉흥 파티 {p+1}", anchor="nw", font=("맑은 고딕", 10, "bold"))
                y_offset += 18
                visible_idx = 0
                for ch in self.adhoc_party[p*4:(p+1)*4]:
                    self.draw_card("즉흥", ch, y_offset, visible_idx)
                    visible_idx += 1
                y_offset += ((visible_idx-1)//COLS + 1) * BOARD_Y_STEP + GROUP_GAP_Y if visible_idx>0 else GROUP_GAP_Y
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            return

        # --- 일반 보드(군별 섹션) ---
        for g in ["1군","2군","3군","4군"]:
            all_chars = list(self.tasks[g].keys())
            if not all_chars: 
                continue
            self.canvas.create_text(12, y_offset, text=f"■ {g}", anchor="nw", font=("맑은 고딕", 10, "bold"))
            y_offset += 18

            visible_idx = 0
            for ch in all_chars:
                tasks = self.tasks[g][ch]
                # 종류/검색 필터 반영
                filtered_for_count = [t for t in tasks if (catf=="전체" or t.get("cat")==catf) and (not kw or kw in (t.get("task","")+t.get("comment","")).lower())]
                if not filtered_for_count and (kw or catf != "전체"):
                    # 필터로 인해 보일 항목 없음 → 카드 스킵
                    continue
                # 태그 필터(AND)
                char_tags = self.buff_select.get(ch, set())
                if active_filters and not all(tag in char_tags for tag in active_filters):
                    continue

                self.draw_card(g, ch, y_offset, visible_idx)
                visible_idx += 1

            y_offset += ((visible_idx-1)//COLS + 1) * BOARD_Y_STEP + GROUP_GAP_Y if visible_idx>0 else GROUP_GAP_Y

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def draw_card(self, g, ch, y_offset, idx):
        tasks = self.tasks[g][ch] if g in self.tasks and ch in self.tasks[g] else []
        done_cnt = sum(1 for t in tasks if t.get("done"))
        total_cnt = len(tasks)
        char_tags = self.buff_select.get(ch, set())

        card_color = GROUP_COLORS[g] if g in GROUP_COLORS else "#CCCCCC"
        card = tk.Frame(self.canvas, width=CARD_W, height=CARD_H, bd=2, relief="ridge", bg=card_color)
        card.pack_propagate(False)
        tk.Label(card, text=f"{ch}", font=("맑은 고딕",10,"bold"), bg=card_color).pack()
        tk.Label(card, text=f"{g} • {done_cnt}/{total_cnt} 완료", bg=card_color).pack()

        row = tk.Frame(card, bg=card_color); row.pack(fill="x", padx=4, pady=2)
        for tag in BUFF_TAGS:
            var = tk.BooleanVar(value=(tag in char_tags))
            chk = tk.Checkbutton(row, text=tag, variable=var,
                                 command=lambda name=ch,t=tag,v=var:self.toggle_buff_tag(name,t,v),
                                 bg=card_color, anchor="w")
            chk.pack(side=tk.LEFT, padx=2)

        # 즉흥 추가 버튼
        tk.Button(card, text="+즉흥", command=lambda name=ch: self.add_to_adhoc(name)).pack(pady=2)

        row_idx = idx // COLS
        col_idx = idx % COLS
        x = 12 + col_idx * BOARD_X_STEP
        y = y_offset + row_idx * BOARD_Y_STEP
        self.canvas.create_window(x, y, window=card, anchor="nw")
    # ================= 즉흥 파티 =================
    def add_to_adhoc(self, name):
        if name not in self.adhoc_party:
            self.adhoc_party.append(name)
        self.render_board()

    def show_adhoc_party(self):
        # 즉흥 파티 보기 (4인 단위로 묶음)
        self.render_board(only_adhoc=True)

    def clear_adhoc_party(self):
        self.adhoc_party.clear()
        self.render_board()
        
    def _on_mousewheel(self, event):
        try:
            if event.num == 4:   # Linux up
                self.canvas.yview_scroll(-3, "units")
            elif event.num == 5: # Linux down
                self.canvas.yview_scroll(3, "units")
            else:                # Windows/macOS
                self.canvas.yview_scroll(int(-1*(event.delta/120))*3, "units")
        except:
            pass

    def toggle_buff_tag(self, name, tag, var):
        if name not in self.buff_select:
            self.buff_select[name] = set()
        if var.get():
            self.buff_select[name].add(tag)
        else:
            self.buff_select[name].discard(tag)
        self.save()
        # 필터가 켜져 있을 수 있으므로 즉시 반영
        self.render_board()

    # ================= CRUD =================
    def add_task(self):
        txt = self.task_entry.get().strip()
        cat = self.cat_add.get()
        if not txt: return
        item = {"task":txt, "done":False, "comment":"", "cat":cat}
        if self.current_character:
            self.tasks[self.current_group][self.current_character].append(item)
        elif self.current_party:
            # 파티에 추가 시, 파티 구성원 전체에 복제 추가
            for ch in self.parties.get(self.current_party, []):
                for g in ["1군","2군","3군","4군"]:
                    if ch in self.tasks[g]:
                        self.tasks[g][ch].append(item.copy())
        self.task_entry.delete(0, tk.END)
        self.save(); self.refresh_views()

    def get_selected_task(self):
        sel = self.tree.selection()
        if not sel: return None, None, None, None
        cat, taskcol, _, _ = self.tree.item(sel[0])["values"]
        try:
            ch  = taskcol[1:taskcol.index("]")]
            txt = taskcol[taskcol.index("]")+2:]
        except: 
            return None, None, None, None
        for g in self.tasks:
            if ch in self.tasks[g]:
                for t in self.tasks[g][ch]:
                    if t.get("task")==txt and t.get("cat")==cat:
                        return g, ch, t, cat
        return None, None, None, None

    def add_comment(self):
        g, ch, t, _ = self.get_selected_task()
        if not t:
            messagebox.showinfo("알림","코멘트를 추가할 숙제를 선택하세요.")
            return
        c = simpledialog.askstring("코멘트", "코멘트:", initialvalue=t.get("comment",""))
        if c is not None:
            t["comment"] = c
            self.save(); self.refresh_views()

    def delete_task(self):
        g, ch, t, _ = self.get_selected_task()
        if not t:
            messagebox.showinfo("알림","삭제할 숙제를 선택하세요.")
            return
        self.tasks[g][ch].remove(t)
        self.save(); self.refresh_views()

    def toggle_all(self):
        entries = []
        if self.current_character:
            entries = self.tasks[self.current_group][self.current_character]
        elif self.current_party:
            for ch in self.parties.get(self.current_party, []):
                for g in ["1군","2군","3군","4군"]:
                    if ch in self.tasks[g]: entries += self.tasks[g][ch]
        if not entries: return
        all_done = all(t.get("done") for t in entries)
        for t in entries:
            t["done"] = not all_done
        self.save(); self.refresh_views()

    # ================= 캐릭터 =================
    def switch_character(self, g):
        self.current_group     = g
        self.current_character = self.char_selectors[g].get() if g=="공통" else self.char_selectors[g].get()
        self.current_party     = None
        self.party_selector.set('')
        self.refresh_views()

    def add_character(self, g):
        n = simpledialog.askstring("캐릭터 추가", f"{g}에 추가할 캐릭터:")
        if not n: return
        if n in self.tasks[g]:
            messagebox.showinfo("알림","이미 존재하는 캐릭터입니다."); return
        self.tasks[g][n] = []
        self.char_selectors[g]["values"] = list(self.tasks[g].keys())
        self.char_selectors[g].set(n)
        self.switch_character(g)
        self.save()

    def delete_character(self, g):
        if g == "공통":
            messagebox.showinfo("알림","공통은 삭제할 수 없습니다."); return
        n = self.char_selectors[g].get()
        if not n or n not in self.tasks[g]:
            messagebox.showinfo("알림","삭제할 캐릭터를 선택하세요."); return
        if not messagebox.askyesno("확인", f"{n} 캐릭터를 {g}에서 삭제할까요?"): return
        del self.tasks[g][n]
        # 파티/태그에서 제거
        for p in list(self.parties.keys()):
            if n in self.parties[p]:
                self.parties[p].remove(n)
        if n in self.buff_select:
            del self.buff_select[n]
        # 콤보 갱신
        self.char_selectors[g]["values"] = list(self.tasks[g].keys())
        self.char_selectors[g].set('')
        self.save(); self.refresh_views()

    def move_character(self, g):
        n = self.char_selectors[g].get()
        if not n:
            messagebox.showinfo("알림","이동할 캐릭터를 선택하세요."); return
        t = simpledialog.askstring("군 이동", "이동할 군 입력 (1군/2군/3군/4군):")
        if t not in self.tasks:
            messagebox.showinfo("알림","잘못된 군 이름입니다."); return
        if t == g: return
        self.tasks[t][n] = self.tasks[g][n]
        del self.tasks[g][n]
        # 콤보 갱신
        self.char_selectors[g]["values"] = list(self.tasks[g].keys()); self.char_selectors[g].set('')
        self.char_selectors[t]["values"] = list(self.tasks[t].keys()); self.char_selectors[t].set(n)
        self.current_group, self.current_character = t, n
        self.save(); self.refresh_views()

    # ================= 파티 =================
    def add_party(self):
        n = simpledialog.askstring("파티 추가","이름:")
        if not n or n in self.parties: return
        self.parties[n] = []
        self.party_selector["values"] = list(self.parties.keys())
        self.party_selector.set(n)
        self.switch_party()
        self.save()

    def delete_party(self):
        p = self.party_selector.get()
        if not p:
            messagebox.showinfo("알림","삭제할 파티를 선택하세요."); return
        if not messagebox.askyesno("확인", f"{p} 파티를 삭제할까요?"): return
        del self.parties[p]
        self.party_selector["values"] = list(self.parties.keys())
        self.party_selector.set('')
        self.current_party = None
        self.save(); self.refresh_views()

    def switch_party(self):
        p = self.party_selector.get()
        if p in self.parties:
            self.current_party     = p
            self.current_character = None
            self.current_group     = None
            self.refresh_views()

    def edit_party(self):
        if not self.current_party:
            messagebox.showinfo("알림","파티를 선택하세요."); return
        all_chars = sorted({ch for g in ["1군","2군","3군","4군"] for ch in self.tasks[g].keys()})
        top = tk.Toplevel(self.root); top.title("파티 편집"); vars = {}
        for i, c in enumerate(all_chars):
            var = tk.BooleanVar(value=(c in self.parties[self.current_party]))
            tk.Checkbutton(top, text=c, variable=var).grid(row=i//3, column=i%3, sticky="w", padx=6, pady=2)
            vars[c] = var
        def save_party():
            self.parties[self.current_party] = [c for c, v in vars.items() if v.get()]
            self.save(); top.destroy(); self.refresh_views()
        tk.Button(top, text="확인", command=save_party).grid(row=(len(all_chars)//3)+1, column=0, columnspan=3, pady=8)

    # ================= 저장/불러오기/기타 =================
    def save(self):
        data = {
            "tasks": self.tasks,
            "parties": self.parties,
            "buff_select": {k:list(v) for k,v in self.buff_select.items()},
        }
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("에러", f"저장 실패: {e}")

    def load_data(self):
        if not os.path.exists(SAVE_FILE): return
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.tasks = data.get("tasks", self.tasks)
            # cat 필드 보정 (구버전 호환)
            for g in self.tasks:
                for ch in self.tasks[g]:
                    for t in self.tasks[g][ch]:
                        if "cat" not in t: t["cat"] = "일일"
            self.parties = data.get("parties", {})
            bs = data.get("buff_select", {})
            self.buff_select = {k:set(v) for k,v in bs.items()}
        except Exception:
            messagebox.showwarning("경고", "저장된 데이터를 불러올 수 없습니다.")

    def reset_filter(self):
        self.filter_entry.delete(0, tk.END)
        self.cat_filter.set("전체")
        self.refresh_views()

    def on_close(self):
        self.save()
        self.root.destroy()


# ---------------- 실행 ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app  = TaskManager(root)
    root.mainloop()
