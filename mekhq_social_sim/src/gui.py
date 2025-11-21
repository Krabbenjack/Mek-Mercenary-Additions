from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, Optional, List
from datetime import date, timedelta, datetime

# Ensure src is on sys.path so the merk_calendar package is importable.
repo_root = Path(__file__).resolve().parents[2]  # mekhq_social_sim/src/gui.py -> repo root
src_path = repo_root.joinpath("src")
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Calendar system imports (required by the full integration)
try:
    from merk_calendar.calendar_system import (
        EventManager,
        RecurrenceType,
        DetailedCalendarWindow,
        DatePickerDialog,
    )
    from merk_calendar.widget import CalendarWidget
except Exception:
    # If calendar package is missing the GUI still runs, calendar features are disabled.
    EventManager = None
    RecurrenceType = None
    DetailedCalendarWindow = None
    DatePickerDialog = None
    CalendarWidget = None

from models import Character
from data_loading import load_personnel  # ensure we can import load_personnel


class MekSocialGUI:
    def __init__(self, master):
        self.master = master
        self.current_date = datetime.now().date()
        self.current_day = 1
        self.characters: Dict[str, Character] = {}
        self.selected_character_id: Optional[str] = None

        # build UI (simplified excerpt)
        right_frame = ttk.Frame(master)
        right_frame.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(right_frame)
        top_bar.pack(fill=tk.X, pady=4)

        # Replace day label with real date label
        self.date_label = ttk.Label(top_bar, text="", padding=4, relief="groove")
        self.date_label.pack(side=tk.LEFT, padx=4)
        self.date_label.bind("<Button-1>", self._on_date_left_click)
        self.date_label.bind("<Button-3>", self._on_date_right_click)
        self._update_date_display()

        next_day_btn = ttk.Button(top_bar, text="Nächster Tag", command=self._next_day)
        next_day_btn.pack(side=tk.LEFT, padx=4)

        import_pers_btn = ttk.Button(
            top_bar, text="Importiere Personal (JSON)", command=self._import_personnel
        )
        import_pers_btn.pack(side=tk.LEFT, padx=4)

        # ... rest of UI setup ...

    def _update_date_display(self):
        text = self.current_date.strftime("%A, %d.%m.%Y")
        self.date_label.config(text=text)

    def _on_date_left_click(self, event):
        if DatePickerDialog is None:
            return
        picker = DatePickerDialog(self.master, self.current_date)
        self.master.wait_window(picker.window)
        if getattr(picker, "result", None):
            self.current_date = picker.result
            self._update_date_display()
            self._update_day_events_bar()
            self._update_day_events_description()

            # Recalculate ages whenever the GUI date changes
            self._update_character_ages()

            # Update details of selected character so displayed age is refreshed
            if self.selected_character_id and self.selected_character_id in self.characters:
                self._update_details(self.characters[self.selected_character_id])

    def _on_date_right_click(self, event):
        if DetailedCalendarWindow is None:
            return
        DetailedCalendarWindow(self.master, self.event_manager, self.current_date)

    def _next_day(self) -> None:
        if not self.characters:
            messagebox.showinfo("Hinweis", "Keine Charaktere geladen.")
            return

        # campaign day counter remains
        self.current_day += 1

        # advance the real date, update displays
        self.current_date += timedelta(days=1)
        self._update_date_display()
        self._update_day_events_bar()
        self._update_day_events_description()

        # Update ages when the day advances
        self._update_character_ages()

        reset_daily_pools(self.characters)
        self._log(f"--- Tag {self.current_day} ---")
        self._log(f"Interaktionspunkte zurückgesetzt.")

        # Update details of the currently selected character
        if self.selected_character_id and self.selected_character_id in self.characters:
            self._update_details(self.characters[self.selected_character_id])

    def _import_personnel(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Select personnel JSON",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            self.characters = load_personnel(file_path)
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", f"Fehler beim Laden der Datei:\n{e}")
            return

        # After loading, compute ages relative to the current GUI date
        self._update_character_ages()

        # Refresh UI lists and selected detail (existing logic)
        self._refresh_character_list()
        if self.selected_character_id and self.selected_character_id in self.characters:
            self._update_details(self.characters[self.selected_character_id])

    def _calculate_age(self, birth_date: date, reference_date: date) -> int:
        """Calculate full years between birth_date and reference_date."""
        if birth_date is None:
            return 0
        age = reference_date.year - birth_date.year
        try:
            # If birthday hasn't happened yet this year, subtract one
            if reference_date < birth_date.replace(year=reference_date.year):
                age -= 1
        except ValueError:
            # handle Feb 29 on non-leap year by comparing month/day manually
            if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
                age -= 1
        return age

    def _update_character_ages(self) -> None:
        """Recalculate ages for all loaded characters using the current GUI date."""
        if not getattr(self, "characters", None):
            return
        for char in self.characters.values():
            bdate = getattr(char, "birthday", None)
            if bdate:
                char.age = self._calculate_age(bdate, self.current_date)

    # Placeholder methods that exist elsewhere in the real file.
    def _update_day_events_bar(self):
        pass

    def _update_day_events_description(self):
        pass

    def _update_details(self, character: Character):
        pass

    def _refresh_character_list(self):
        pass

    def _log(self, message: str):
        print(message)


# If running standalone
if __name__ == "__main__":
    root = tk.Tk()
    app = MekSocialGUI(root)
    root.mainloop()
