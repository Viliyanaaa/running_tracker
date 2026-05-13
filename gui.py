import customtkinter as ctk
from tkinter import ttk, messagebox
from database import create_table, add_run, get_all_runs, delete_run, get_stats, format_pace, get_best_month, get_best_race, format_time
from charts import create_distance_chart
from datetime import datetime

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class LaufTrackerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🏃 Lauf Tracker")
        self.geometry("900x600")

        create_table()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_area.grid_rowconfigure(2, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self._build_sidebar()
        self._build_dashboard()
        self._build_table()
        self._build_chart()
        self.refresh_data()

    def _build_sidebar(self):
        ctk.CTkLabel(self.sidebar, text="🏃 Lauf Tracker",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 15))

        ctk.CTkLabel(self.sidebar, text="Datum (JJJJ-MM-TT)").pack(padx=20, anchor="w")
        self.entry_date = ctk.CTkEntry(self.sidebar, placeholder_text="z.B. 2024-05-12")
        self.entry_date.pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(self.sidebar, text="Distanz (km)").pack(padx=20, anchor="w")
        self.entry_distance = ctk.CTkEntry(self.sidebar, placeholder_text="z.B. 5.5")
        self.entry_distance.pack(padx=20, pady=(0, 10), fill="x")

        ctk.CTkLabel(self.sidebar, text="Dauer (Minuten)").pack(padx=20, anchor="w")
        self.entry_duration = ctk.CTkEntry(self.sidebar, placeholder_text="z.B. 30")
        self.entry_duration.pack(padx=20, pady=(0, 15), fill="x")

        ctk.CTkButton(self.sidebar, text="➕ Lauf speichern",
                      command=self.save_run).pack(padx=20, fill="x")

        ctk.CTkButton(self.sidebar, text="🗑 Lauf löschen",
                      fg_color="#c0392b", hover_color="#e74c3c",
                      command=self.delete_selected).pack(padx=20, pady=(8, 0), fill="x")
        
        ctk.CTkLabel(self.sidebar, text="Notizen (optional)").pack(padx=20, anchor="w")
        self.entry_notes = ctk.CTkEntry(self.sidebar, placeholder_text="z.B. Morgenrunde")
        self.entry_notes.pack(padx=20, pady=(0, 15), fill="x")

    def _build_dashboard(self):
        dash = ctk.CTkFrame(self.main_area, fg_color="transparent")
        dash.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        dash.grid_columnconfigure((0,1,2,3), weight=1)

        self.stat_cards = {}

        # Горен ред – основни статистики
        top_cards = [
            ("total_runs", "🏅 Läufe",          "0"),
            ("total_km",   "📏 Gesamt km",       "0.0"),
            ("avg_pace",   "⏱ Ø Tempo (min/km)", "0:00"),
            ("best_pace",  "⚡ Bestes Tempo",    "0:00"),
        ]
        for i, (key, label, default) in enumerate(top_cards):
            card = ctk.CTkFrame(dash)
            card.grid(row=0, column=i, padx=5, pady=(0,5), sticky="ew")
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11)).pack(pady=(10,2))
            val = ctk.CTkLabel(card, text=default, font=ctk.CTkFont(size=22, weight="bold"))
            val.pack(pady=(0,10))
            self.stat_cards[key] = val

        # Долен ред – разширени статистики
        dash2 = ctk.CTkFrame(self.main_area, fg_color="transparent")
        dash2.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        dash2.grid_columnconfigure((0,1,2,3,4), weight=1)

        bottom_cards = [
            ("best_month", "📅 Bester Monat",    "—"),
            ("best_5k",    "🥇 Beste 5 km",      "—"),
            ("best_10k",   "🥇 Beste 10 km",     "—"),
            ("best_half",  "🥇 Halbmarathon",    "—"),
            ("best_full",  "🏆 Marathon",         "—"),
        ]
        for i, (key, label, default) in enumerate(bottom_cards):
            card = ctk.CTkFrame(dash2)
            card.grid(row=0, column=i, padx=5, sticky="ew")
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=11)).pack(pady=(10,2))
            val = ctk.CTkLabel(card, text=default, font=ctk.CTkFont(size=14, weight="bold"))
            val.pack(pady=(0,10))
            self.stat_cards[key] = val

    #TABELLE
    def _build_table(self):
        table_frame = ctk.CTkFrame(self.main_area)
        table_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Stil für die Tabelle
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#2b2b2b",
                        foreground="white",
                        rowheight=28,
                        fieldbackground="#2b2b2b",
                        bordercolor="#2b2b2b",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background="#1f1f1f",
                        foreground="white",
                        relief="flat")
        style.map("Treeview",
                  background=[("selected", "#4CAF50")],
                  foreground=[("selected", "white")])

        columns = ("id", "date", "distance", "duration", "pace", "notes")
        self.table = ttk.Treeview(table_frame, columns=columns,
                                   show="headings", selectmode="browse")

        # Spalten definieren
        self.table.heading("id",       text="ID")
        self.table.heading("date",     text="Datum")
        self.table.heading("distance", text="Distanz (km)")
        self.table.heading("duration", text="Dauer (min)")
        self.table.heading("pace",     text="Tempo (min/km)")
        self.table.heading("notes",    text="Notizen")

        self.table.column("id",       width=40,  anchor="center")
        self.table.column("date",     width=100, anchor="center")
        self.table.column("distance", width=110, anchor="center")
        self.table.column("duration", width=110, anchor="center")
        self.table.column("pace",     width=120, anchor="center")
        self.table.column("notes",    width=180, anchor="w")

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                   command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    #DIAGRAMM
    def _build_chart(self):
        self.chart_frame = ctk.CTkFrame(self.main_area)
        self.chart_frame.grid(row=3, column=0, sticky="ew", pady=(0, 5))

    #LOGIK
    def save_run(self):
        date     = self.entry_date.get().strip()
        distance = self.entry_distance.get().strip()
        duration = self.entry_duration.get().strip()
        notes = self.entry_notes.get().strip()

        # Validierung
        if not date or not distance or not duration:
            messagebox.showwarning("Fehlende Daten",
                                   "Bitte Datum, Distanz und Dauer ausfüllen.")
            return

        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Falsches Format",
                                 "Datum muss im Format JJJJ-MM-TT sein.\nz.B. 2024-05-12")
            return

        try:
            distance = float(distance)
            duration = float(duration)
            if distance <= 0 or duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ungültige Werte",
                                 "Distanz und Dauer müssen positive Zahlen sein.")
            return

        add_run(date, distance, duration, notes)
        self._clear_inputs()
        self.refresh_data()

    def delete_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Nichts ausgewählt",
                                   "Bitte einen Lauf in der Tabelle auswählen.")
            return

        confirm = messagebox.askyesno("Löschen bestätigen",
                                       "Möchtest du diesen Lauf wirklich löschen?")
        if confirm:
            run_id = self.table.item(selected[0])["values"][0]
            delete_run(run_id)
            self.refresh_data()

    def refresh_data(self):
        # Tabelle leeren und neu befüllen
        for row in self.table.get_children():
            self.table.delete(row)

        runs = get_all_runs()
        for run in runs:
            self.table.insert("", "end", values=(
                run["id"],
                run["date"],
                f'{run["distance_km"]} km',
                f'{run["duration_min"]} min',
                f'{format_pace(run["pace"])} min/km',
                run["notes"] or "—"
            ))

        # Statistiken aktualisieren
        stats = get_stats()
        if stats and stats["total_runs"] > 0:
            self.stat_cards["total_runs"].configure(text=str(stats["total_runs"]))
            self.stat_cards["total_km"].configure(text=f'{stats["total_km"]} km')
            self.stat_cards["avg_pace"].configure(text=format_pace(stats["avg_pace"]))
            self.stat_cards["best_pace"].configure(text=format_pace(stats["best_pace"]))

        best_month = get_best_month()
        if best_month and best_month["total_km"]:
            self.stat_cards["best_month"].configure(
            text=f'{best_month["month"]}\n{best_month["total_km"]} km')

        # Distanz
        races = [
            ("best_5k",   4.8,  5.2,  "Kein 5km"),
            ("best_10k",  9.8, 10.2,  "Kein 10km"),
            ("best_half", 21.0, 21.3, "Kein Halbmarathon"),
            ("best_full", 42.0, 42.3, "Kein Marathon"),
        ]
        for key, min_km, max_km, empty_text in races:
            result = get_best_race(min_km, max_km)
            if result and result["best_time"]:
                self.stat_cards[key].configure(text=format_time(result["best_time"]))
            else:
                self.stat_cards[key].configure(text=empty_text)

        # Diagramm aktualisieren
        create_distance_chart(self.chart_frame, runs)

    def _clear_inputs(self):
        self.entry_date.delete(0, "end")
        self.entry_distance.delete(0, "end")
        self.entry_duration.delete(0, "end")
        self.entry_notes.delete(0, "end")