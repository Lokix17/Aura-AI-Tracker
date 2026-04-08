import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from plyer import notification
import json, os, re

# --- SETTINGS ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(BASE_DIR, "data.json")

class AuraEpicTracker(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AURA AI | Epic Financial & Habit HUD")
        self.geometry("1300x920")
        self.configure(fg_color="#0a0a0a")

        self.data = self.load_data()
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---------------- SIDEBAR ----------------
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#0d0d0d")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="AURA AI", font=ctk.CTkFont(size=28, weight="bold"), text_color="#3b8ed0").grid(row=0, column=0, padx=20, pady=40)

        # Navigation Buttons
        self.create_btn("📊 Set Monthly Goal", self.set_budget_window, 1)
        self.create_btn("💰 Add Income", self.add_income_window, 2, color="#6c5ce7") # Purple for Income
        self.create_btn("💸 Add Expense", self.add_expense_window, 3, primary=True)
        self.create_btn("✨ New Habit", self.add_habit_window, 4)
        
        # Sidebar Stats
        self.score_frame = ctk.CTkFrame(self.sidebar, fg_color="#161616", corner_radius=15)
        self.score_frame.grid(row=5, column=0, padx=20, pady=30, sticky="ew")
        self.score_lbl = ctk.CTkLabel(self.score_frame, text="Consistency: 0%", font=ctk.CTkFont(size=14, weight="bold"))
        self.score_lbl.pack(pady=15)

        self.create_btn("🔄 Wipe All Data", self.reset_data, 10, color="#333")

        # ---------------- MAIN DASHBOARD ----------------
        self.main = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, padx=25, pady=0, sticky="nsew")
        self.main.grid_columnconfigure((0, 1, 2), weight=1)

        # Header
        ctk.CTkLabel(self.main, text="Financial Intelligence HUD", font=ctk.CTkFont(size=30, weight="bold")).grid(row=0, column=0, columnspan=3, pady=(30, 10), sticky="w")

        # The 3-Card Stat System
        self.card_budget = self.create_card("MONTHLY GOAL", 0, 1, "#3b8ed0")
        self.card_spent = self.create_card("TOTAL SPENT", 1, 1, "#e74c3c")
        self.card_cash = self.create_card("CASH REMAINING", 2, 1, "#2ecc71")

        # Habit Action Row
        ctk.CTkLabel(self.main, text="Daily Habit Protocols", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3b8ed0").grid(row=2, column=0, columnspan=3, pady=(30, 5), sticky="w")
        self.habit_action_area = ctk.CTkFrame(self.main, fg_color="transparent")
        self.habit_action_area.grid(row=3, column=0, columnspan=3, sticky="ew")

        # Data Tables
        ctk.CTkLabel(self.main, text="Transaction History", font=ctk.CTkFont(size=18, weight="bold")).grid(row=4, column=0, columnspan=2, pady=(30, 5), sticky="w")
        ctk.CTkLabel(self.main, text="Schedule", font=ctk.CTkFont(size=18, weight="bold")).grid(row=4, column=2, pady=(30, 5), sticky="w", padx=(10,0))

        self.tree_ex = self.create_tree(self.main, ("Name", "Amount", "Date"), 5, 0, span=2)
        self.tree_hb = self.create_tree(self.main, ("Habit", "Time", "Status"), 5, 2, left_pad=10)

        self.update_ui()
        self.check_loops()

    # --- UI HELPERS ---
    def create_btn(self, txt, cmd, row, primary=False, color=None):
        btn = ctk.CTkButton(self.sidebar, text=txt, font=ctk.CTkFont(size=14, weight="bold"), height=48, corner_radius=12,
                            fg_color=color if color else ("#3b8ed0" if primary else "transparent"),
                            border_width=0 if (primary or color) else 1, command=cmd)
        btn.grid(row=row, column=0, padx=20, pady=10, sticky="ew")

    def create_card(self, title, col, row, color):
        f = ctk.CTkFrame(self.main, fg_color="#111111", corner_radius=15, border_width=1, border_color="#222")
        f.grid(row=row, column=col, padx=8, pady=10, sticky="nsew")
        ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color="gray").pack(pady=(15, 0))
        lbl = ctk.CTkLabel(f, text="₹0", font=ctk.CTkFont(size=26, weight="bold"), text_color=color)
        lbl.pack(pady=(0, 20))
        return lbl

    def create_tree(self, parent, cols, row, col, span=1, left_pad=0):
        frame = ctk.CTkFrame(parent, fg_color="#111111", corner_radius=12)
        frame.grid(row=row, column=col, columnspan=span, sticky="nsew", pady=5, padx=(left_pad, 0))
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#111111", foreground="white", fieldbackground="#111111", rowheight=32)
        style.configure("Treeview.Heading", background="#222", foreground="#3b8ed0", font=('Arial', 9, 'bold'))
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, anchor="center")
        tree.pack(expand=True, fill="both", padx=8, pady=8)
        return tree

    # --- EPIC DATA LOGIC ---
    def load_data(self):
        if os.path.exists(FILE):
            try:
                with open(FILE, "r") as f: return json.load(f)
            except: pass
        # Initial Structure includes 'funds'
        return {"expenses": [], "habits": [], "budget": 0, "funds": 0}

    def save_data(self):
        with open(FILE, "w") as f: json.dump(self.data, f, indent=4)

    def update_ui(self):
        exp = self.data.get("expenses", [])
        budget_goal = float(self.data.get("budget", 0))
        total_funds = float(self.data.get("funds", 0))
        spent = sum(float(x[1]) for x in exp)
        
        # Epic Logic: Cash Remaining is Total Income minus Spent
        cash_left = total_funds - spent

        self.card_budget.configure(text=f"₹{budget_goal:,.2f}")
        self.card_spent.configure(text=f"₹{spent:,.2f}")
        self.card_cash.configure(text=f"₹{cash_left:,.2f}")

        # Budget Warning (Based on the fixed Goal)
        if budget_goal > 0 and spent > (budget_goal * 0.9):
            self.card_spent.configure(text_color="#ff7675")

        # Update Tables
        for i in self.tree_ex.get_children(): self.tree_ex.delete(i)
        for e in reversed(exp[-12:]): self.tree_ex.insert("", "end", values=e)

        # Habit Refresh
        for i in self.tree_hb.get_children(): self.tree_hb.delete(i)
        for widget in self.habit_action_area.winfo_children(): widget.destroy()
        
        habits = self.data.get("habits", [])
        completed_count = 0
        for idx, h in enumerate(habits):
            is_done = h[3] if len(h) > 3 else False
            if is_done: completed_count += 1
            self.tree_hb.insert("", "end", values=(h[0], h[2], "Done" if is_done else "Pending"))

            # Habit Button
            card = ctk.CTkFrame(self.habit_action_area, fg_color="#161616" if not is_done else "#0f2015", width=160)
            card.pack(side="left", padx=8, pady=5)
            ctk.CTkLabel(card, text=h[0][:15], font=ctk.CTkFont(size=12, weight="bold")).pack(pady=5, padx=10)
            btn = ctk.CTkButton(card, text="Complete" if not is_done else "Undo", width=70, height=22, 
                                fg_color="#3b8ed0" if not is_done else "#2ecc71", 
                                command=lambda i=idx: self.toggle_habit(i))
            btn.pack(pady=(0, 10))

        if habits:
            self.score_lbl.configure(text=f"Consistency: {int((completed_count/len(habits))*100)}%")

    def toggle_habit(self, idx):
        if len(self.data["habits"][idx]) < 4: self.data["habits"][idx].append(True)
        else: self.data["habits"][idx][3] = not self.data["habits"][idx][3]
        self.save_data(); self.update_ui()

    def check_loops(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for h in self.data.get("habits", []):
            if now == f"{h[1]} {h[2]}":
                notification.notify(title="AURA Habit Alert", message=f"Execute Protocol: {h[0]}")
        self.after(60000, self.check_loops)

    # --- POPUPS ---
    def set_budget_window(self):
        res = ctk.CTkInputDialog(text="Enter Monthly Budget Goal (₹):", title="Strategy").get_input()
        if res:
            try:
                self.data["budget"] = float(re.sub(r"[^\d.]", "", res))
                self.save_data(); self.update_ui()
            except: pass

    def add_income_window(self):
        res = ctk.CTkInputDialog(text="Enter Income/Add Funds (₹):", title="Wealth Injection").get_input()
        if res:
            try:
                # Additively increase funds
                amount = float(re.sub(r"[^\d.]", "", res))
                self.data["funds"] = self.data.get("funds", 0) + amount
                self.save_data(); self.update_ui()
                notification.notify(title="Funds Synced", message=f"Added ₹{amount} to wallet.")
            except: pass

    def add_expense_window(self):
        w = ctk.CTkToplevel(self); w.geometry("380x400"); w.attributes("-topmost", True); w.configure(fg_color="#0d0d0d")
        ctk.CTkLabel(w, text="Log Transaction", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=25)
        name = ctk.CTkEntry(w, placeholder_text="Details", height=45); name.pack(pady=10, padx=35, fill="x")
        amt = ctk.CTkEntry(w, placeholder_text="Amount (₹)", height=45); amt.pack(pady=10, padx=35, fill="x")
        def save():
            if name.get() and amt.get():
                try:
                    price = float(re.sub(r"[^\d.]", "", amt.get()))
                    self.data["expenses"].append([name.get(), price, datetime.now().strftime("%d %b, %H:%M")])
                    self.save_data(); self.update_ui(); w.destroy()
                    
                    # Alert Check
                    budget = self.data.get("budget", 0)
                    spent = sum(float(x[1]) for x in self.data["expenses"])
                    if budget > 0 and spent > (budget * 0.9):
                        notification.notify(title="ALERT", message="You have exceeded 90% of your budget goal!")
                except: pass
        ctk.CTkButton(w, text="Confirm", command=save, height=45).pack(pady=30)

    def add_habit_window(self):
        w = ctk.CTkToplevel(self); w.geometry("380x520"); w.attributes("-topmost", True); w.configure(fg_color="#0d0d0d")
        ctk.CTkLabel(w, text="New Habit Sync", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=25)
        name = ctk.CTkEntry(w, placeholder_text="Protocol Name", height=45); name.pack(pady=10, padx=35, fill="x")
        time_e = ctk.CTkEntry(w, placeholder_text="Time (e.g. 7:00 PM or 19:00)", height=45); time_e.pack(pady=10, padx=35, fill="x")
        cal = DateEntry(w); cal.pack(pady=20)
        def save():
            raw_t = time_e.get().strip().upper()
            if name.get() and raw_t:
                try:
                    if "AM" in raw_t or "PM" in raw_t:
                        ft = datetime.strptime(raw_t, "%I:%M %p").strftime("%H:%M")
                    else:
                        ft = datetime.strptime(raw_t, "%H:%M").strftime("%H:%M")
                    self.data["habits"].append([name.get(), cal.get_date().strftime("%Y-%m-%d"), ft, False])
                    self.save_data(); self.update_ui(); w.destroy()
                except: messagebox.showerror("Error", "Invalid Time Format")
        ctk.CTkButton(w, text="Authorize", command=save, height=45).pack(pady=20)

    def reset_data(self):
        if messagebox.askyesno("Confirm", "Purge all data from system?"):
            self.data = {"expenses": [], "habits": [], "budget": 0, "funds": 0}
            self.save_data(); self.update_ui()

if __name__ == "__main__":
    app = AuraEpicTracker()
    app.mainloop()