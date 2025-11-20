import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
from datetime import datetime, date
from tkcalendar import Calendar


class CalendarDialog(tk.Toplevel):
    def __init__(self, master, initial_date=None):
        super().__init__(master)
        self.title("Datum wählen")
        self.resizable(False, False)
        self.selected_date = None

        if initial_date is None:
            initial_date = date.today()

        # tkcalendar-Widget
        self.cal = Calendar(
            self,
            selectmode="day",
            year=initial_date.year,
            month=initial_date.month,
            day=initial_date.day,
            date_pattern="dd.mm.yyyy",  # Format wie im Formular
        )
        self.cal.pack(padx=10, pady=10)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=(0, 10))

        ttk.Button(btn_frame, text="OK", command=self.on_ok).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Abbrechen", command=self.on_cancel).pack(
            side="left", padx=5
        )

        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def on_ok(self):
        # gibt einen String im Format dd.mm.yyyy zurück
        self.selected_date = self.cal.get_date()
        self.destroy()

    def on_cancel(self):
        self.selected_date = None
        self.destroy()


class InvoiceWindow(tk.Toplevel):
    def __init__(self, master, bookings):
        super().__init__(master)
        self.title("Rechnung")
        self.resizable(False, False)

        ttk.Label(self, text="Rechnung",
                  font=("TkDefaultFont", 11, "bold")).grid(
            row=0, column=0, columnspan=3, pady=(10, 5)
        )

        # Tabellenkopf
        ttk.Label(self, text="Art", borderwidth=1, relief="solid",
                  width=18, anchor="w").grid(row=1, column=0, sticky="nsew")
        ttk.Label(self, text="Zeitraum", borderwidth=1, relief="solid",
                  width=25, anchor="w").grid(row=1, column=1, sticky="nsew")
        ttk.Label(self, text="Betrag in €", borderwidth=1, relief="solid",
                  width=12, anchor="e").grid(row=1, column=2, sticky="nsew")

        total = 0.0
        for i, b in enumerate(bookings, start=2):
            art, zeitraum, betrag = b
            ttk.Label(self, text=art, borderwidth=1, relief="solid",
                      anchor="w").grid(row=i, column=0, sticky="nsew")
            ttk.Label(self, text=zeitraum, borderwidth=1, relief="solid",
                      anchor="w").grid(row=i, column=1, sticky="nsew")
            ttk.Label(self, text=betrag, borderwidth=1, relief="solid",
                      anchor="e").grid(row=i, column=2, sticky="nsew")
            total += float(str(betrag).replace(",", "."))

        i = len(bookings) + 2
        ttk.Label(self,
                  text=f"Gesamtbetrag (Euro): {total:0.2f}".replace(".", ","),
                  font=("TkDefaultFont", 10, "bold")).grid(
            row=i, column=0, columnspan=3, sticky="e", padx=5, pady=(5, 10)
        )

        ttk.Button(self, text="Schließen",
                   command=self.destroy).grid(row=i + 1, column=0,
                                              columnspan=3, pady=(0, 10))

        for col in range(3):
            self.grid_columnconfigure(col, weight=1)


class BookingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Buchungsabrechnung")

        self.n_rows = 3

        self.check_vars = []
        self.check_buttons = []
        self.combos = []
        self.entry_from = []
        self.entry_to = []
        self.entry_price = []
        self.btn_from = []
        self.btn_to = []

        self.clear_mode = False
        self.backup_state = None

        # --- NEU: Style und Grundfarbe -----------------------------------
        self.style = ttk.Style(self.root)
        # Startfarbe (Standard-Hintergrund des Fensters)
        self.primary_color = self.root.cget("bg")

        self._create_menubar()
        self.build_ui()
        self.apply_colors()  # Styles an die Startfarbe anpassen
        self.update_rows_from_checks()

    # --- NEU: Menü + Colorwheel ------------------------------------------

    def _create_menubar(self):
        menubar = tk.Menu(self.root)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(
            label="Farbschema...",
            command=self.choose_color
        )
        menubar.add_cascade(label="Einstellungen", menu=settings_menu)

        self.root.config(menu=menubar)

    def choose_color(self):
        """Öffnet den Farb-Dialog (RGB-Colorwheel) und aktualisiert die UI."""
        color = colorchooser.askcolor(
            initialcolor=self.primary_color,
            parent=self.root,
            title="Farbschema wählen"
        )[1]
        if color:
            self.primary_color = color
            self.apply_colors()

    def apply_colors(self):
        """Wendet die aktuell gewählte Farbe auf die wichtigsten Styles an."""
        # Hintergrund des Hauptfensters
        self.root.configure(bg=self.primary_color)

        # ttk-Styles global anpassen (wir verwenden Standard-Styles)
        self.style.configure("TFrame", background=self.primary_color)
        self.style.configure("TLabelframe", background=self.primary_color)
        self.style.configure("TLabel", background=self.primary_color)
        self.style.configure("TCheckbutton", background=self.primary_color)
        # Buttons und andere Controls – je nach Theme wird background
        # nicht immer 1:1 übernommen, aber es gibt i.d.R. einen sichtbaren Effekt.
        self.style.configure("TButton", background=self.primary_color)
        self.style.configure("TMenubutton", background=self.primary_color)

    # --- UI-Aufbau --------------------------------------------------------

    def build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)

        ttk.Label(main, text="Buchungsabrechnung",
                  font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, columnspan=7, pady=(0, 10)
        )

        # Kopfzeile
        ttk.Label(main, text="Art").grid(row=1, column=1, padx=5)
        ttk.Label(main, text="Vom").grid(row=1, column=2, padx=5)
        ttk.Label(main, text="Bis").grid(row=1, column=4, padx=5)
        ttk.Label(main, text="Preis in Euro").grid(row=1, column=6, padx=5)

        for i in range(self.n_rows):
            row = i + 2  # Zeile im Grid

            var = tk.IntVar(value=0)
            chk = ttk.Checkbutton(
                main, variable=var,
                command=lambda idx=i: self.on_check_toggled(idx)
            )
            chk.grid(row=row, column=0, padx=5)
            self.check_vars.append(var)
            self.check_buttons.append(chk)

            combo = ttk.Combobox(
                main,
                values=["Vollpension", "Halbpension", "Spezialangebot"],
                state="readonly",
                width=18,
            )
            combo.grid(row=row, column=1, padx=5, pady=2)
            self.combos.append(combo)

            e_from = ttk.Entry(main, width=12)
            e_from.grid(row=row, column=2, padx=2)
            self.entry_from.append(e_from)

            b_from = ttk.Button(
                main, text="...", width=3,
                command=lambda ent=e_from: self.open_calendar(ent)
            )
            b_from.grid(row=row, column=3, padx=2)
            self.btn_from.append(b_from)

            e_to = ttk.Entry(main, width=12)
            e_to.grid(row=row, column=4, padx=2)
            self.entry_to.append(e_to)

            b_to = ttk.Button(
                main, text="...", width=3,
                command=lambda ent=e_to: self.open_calendar(ent)
            )
            b_to.grid(row=row, column=5, padx=2)
            self.btn_to.append(b_to)

            e_price = ttk.Entry(main, width=10)
            e_price.grid(row=row, column=6, padx=5)
            e_price.insert(0, "0,00")
            self.entry_price.append(e_price)

        # Buttonleiste
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=self.n_rows + 3, column=0,
                       columnspan=7, pady=(10, 0))

        self.btn_clear = ttk.Button(btn_frame, text="Clear",
                                    command=self.on_clear)
        self.btn_clear.pack(side="left", padx=5)

        self.btn_invoice = ttk.Button(btn_frame, text="Rechnung anzeigen",
                                      command=self.show_invoice)
        self.btn_invoice.pack(side="left", padx=5)

        ttk.Button(btn_frame, text="Beenden",
                   command=self.root.destroy).pack(side="left", padx=5)

        # Anfangszustand: nur erste Checkbox auswählbar
        for i in range(1, self.n_rows):
            self.check_buttons[i]["state"] = tk.DISABLED

    # --- Zeilen-Handling -------------------------------------------------

    def set_row_enabled(self, idx, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.combos[idx]["state"] = "readonly" if enabled else tk.DISABLED
        self.entry_from[idx]["state"] = state
        self.entry_to[idx]["state"] = state
        self.entry_price[idx]["state"] = state
        self.btn_from[idx]["state"] = state
        self.btn_to[idx]["state"] = state

    def clear_row(self, idx):
        self.combos[idx].set("")
        self.entry_from[idx].delete(0, tk.END)
        self.entry_to[idx].delete(0, tk.END)
        self.entry_price[idx].delete(0, tk.END)
        self.entry_price[idx].insert(0, "0,00")

    def copy_row(self, src, dest):
        self.combos[dest].set(self.combos[src].get())
        self.entry_from[dest].delete(0, tk.END)
        self.entry_from[dest].insert(0, self.entry_from[src].get())
        self.entry_to[dest].delete(0, tk.END)
        self.entry_to[dest].insert(0, self.entry_to[src].get())
        self.entry_price[dest].delete(0, tk.END)
        self.entry_price[dest].insert(0, self.entry_price[src].get())

    def compress_rows(self, start):
        """Beim Abwählen: nachfolgende Zeilen nach oben rücken."""
        for j in range(start, self.n_rows - 1):
            self.copy_row(j + 1, j)
            self.check_vars[j].set(self.check_vars[j + 1].get())
        last = self.n_rows - 1
        self.check_vars[last].set(0)
        self.clear_row(last)

    def update_rows_from_checks(self):
        active_indices = [i for i in range(self.n_rows)
                          if self.check_vars[i].get() == 1]

        for i in range(self.n_rows):
            enabled = self.check_vars[i].get() == 1
            self.set_row_enabled(i, enabled)

        if active_indices:
            last_active = active_indices[-1]
        else:
            last_active = -1

        # Checkbox-Freigabe: nur erste + nächste freie Zeile auswählbar
        for i in range(self.n_rows):
            if i == 0:
                self.check_buttons[i]["state"] = tk.NORMAL
            elif i <= last_active + 1:
                self.check_buttons[i]["state"] = tk.NORMAL
            else:
                self.check_buttons[i]["state"] = tk.DISABLED

    def on_check_toggled(self, idx):
        if self.check_vars[idx].get() == 0:
            # abgewählt -> Zeilen nach oben rücken
            self.compress_rows(idx)
        self.update_rows_from_checks()

    # --- Datum / Kalender -------------------------------------------------

    def open_calendar(self, entry_widget):
        current_text = entry_widget.get()
        try:
            from datetime import datetime
            current_date = datetime.strptime(current_text, "%d.%m.%Y").date()
        except ValueError:
            current_date = date.today()

        dlg = CalendarDialog(self.root, current_date)
        self.root.wait_window(dlg)
        if dlg.selected_date:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, dlg.selected_date)

    # --- Rechnung ---------------------------------------------------------

    def show_invoice(self):
        bookings = []

        for i in range(self.n_rows):
            if self.check_vars[i].get() != 1:
                continue

            art = self.combos[i].get()
            if not art:
                messagebox.showerror(
                    "Fehler", f"Bitte Art in Zeile {i + 1} wählen."
                )
                return

            von_text = self.entry_from[i].get()
            bis_text = self.entry_to[i].get()

            try:
                von = datetime.strptime(von_text, "%d.%m.%Y").date()
            except ValueError:
                messagebox.showerror(
                    "Fehler", f"Ungültiges Startdatum in Zeile {i + 1}."
                )
                return

            try:
                bis = datetime.strptime(bis_text, "%d.%m.%Y").date()
            except ValueError:
                messagebox.showerror(
                    "Fehler", f"Ungültiges Enddatum in Zeile {i + 1}."
                )
                return

            if bis <= von:
                messagebox.showerror(
                    "Fehler",
                    f"Enddatum muss nach dem Anfangsdatum liegen (Zeile {i + 1}).",
                )
                return

            preis_text = self.entry_price[i].get().strip().replace(" ", "")
            preis_text_norm = preis_text.replace(",", ".")

            try:
                preis = float(preis_text_norm)
            except ValueError:
                messagebox.showerror(
                    "Fehler", f"Ungültiger Preis in Zeile {i + 1}."
                )
                return

            if preis < 0:
                messagebox.showerror(
                    "Fehler",
                    f"Preis muss mindestens 0,00 sein (Zeile {i + 1}).",
                )
                return

            preis = round(preis, 2)
            preis_str = f"{preis:0.2f}".replace(".", ",")

            zeitraum = f"{von.strftime('%d.%m.%Y')}–{bis.strftime('%d.%m.%Y')}"
            bookings.append((art, zeitraum, preis_str))

        if not bookings:
            messagebox.showinfo("Hinweis", "Es wurde keine Buchung ausgewählt.")
            return

        InvoiceWindow(self.root, bookings)

    # --- Clear / Zurück ---------------------------------------------------

    def on_clear(self):
        if not self.clear_mode:
            # Zustand sichern
            self.backup_state = []
            for i in range(self.n_rows):
                self.backup_state.append(
                    {
                        "checked": self.check_vars[i].get(),
                        "art": self.combos[i].get(),
                        "von": self.entry_from[i].get(),
                        "bis": self.entry_to[i].get(),
                        "preis": self.entry_price[i].get(),
                    }
                )

            # Alles löschen
            for i in range(self.n_rows):
                self.check_vars[i].set(0)
                self.clear_row(i)

            self.update_rows_from_checks()
            self.clear_mode = True
            self.btn_clear.config(text="Zurück")

        else:
            # Zustand wiederherstellen
            if self.backup_state is not None:
                for i in range(self.n_rows):
                    st = self.backup_state[i]
                    self.check_vars[i].set(st["checked"])
                    self.combos[i].set(st["art"])
                    self.entry_from[i].delete(0, tk.END)
                    self.entry_from[i].insert(0, st["von"])
                    self.entry_to[i].delete(0, tk.END)
                    self.entry_to[i].insert(0, st["bis"])
                    self.entry_price[i].delete(0, tk.END)
                    self.entry_price[i].insert(0, st["preis"])

            self.update_rows_from_checks()
            self.clear_mode = False
            self.btn_clear.config(text="Clear")


if __name__ == "__main__":
    root = tk.Tk()
    app = BookingApp(root)
    root.mainloop()
