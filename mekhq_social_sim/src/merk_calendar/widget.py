"""
CalendarWidget - embeddable calendar control for the main UI.

Usage:
    from merk_calendar import EventManager
    from merk_calendar.widget import CalendarWidget

    # inside your main UI creation code (for example in gui.py)
    event_manager = EventManager()              # or reuse an existing manager
    cal = CalendarWidget(parent_frame, event_manager=event_manager)
    cal.pack(anchor="ne")                       # place top-right as desired

Behavior:
- Left-click opens the date picker (Button-1)
- Right-click opens the detailed calendar (Button-3)
- Calls optional on_date_change callback when the displayed date changes
"""
import sys
from pathlib import Path
import tkinter as tk
from datetime import datetime

# Try package import; if running from repo without installed package, add src to sys.path
try:
    from merk_calendar.calendar_system import DatePickerDialog, DetailedCalendarWindow, EventManager
except Exception:
    repo_root = Path(__file__).resolve().parents[2]  # repo/src/merk_calendar/widget.py -> repo root
    src_dir = repo_root.joinpath("src")
    sys.path.insert(0, str(src_dir))
    from merk_calendar.calendar_system import DatePickerDialog, DetailedCalendarWindow, EventManager


class CalendarWidget(tk.Frame):
    def __init__(self, parent, event_manager: EventManager = None, initial_date=None, on_date_change=None, **kwargs):
        """
        parent: tk container
        event_manager: optional EventManager instance (if None a new one is created)
        initial_date: optional datetime.date to start with
        on_date_change: optional callback fn(new_date) when date changes
        kwargs: forwarded to tk.Frame
        """
        super().__init__(parent, **kwargs)
        self.event_manager = event_manager or EventManager()
        self.on_date_change = on_date_change
        self.current_date = initial_date or datetime.now().date()

        # Compact visual appearance for embedding in a top bar
        self.configure(bg=self["bg"])

        # Weekday (small)
        self.weekday_label = tk.Label(self, text="", font=("Arial", 10), padx=6, pady=1)
        self.weekday_label.pack(anchor="e")

        # Date label (DD.MM.YYYY)
        self.date_label = tk.Label(self, text="", font=("Arial", 11, "bold"), padx=6, pady=1)
        self.date_label.pack(anchor="e")

        # Hint line
        self.hint_label = tk.Label(self, text="Left: pick   Right: calendar", font=("Arial", 8), fg="gray")
        self.hint_label.pack(anchor="e", pady=(1, 0))

        # Bind left and right clicks (left: open picker, right: open detailed view)
        self.weekday_label.bind("<Button-1>", self._on_left_click)
        self.weekday_label.bind("<Button-3>", self._on_right_click)
        self.date_label.bind("<Button-1>", self._on_left_click)
        self.date_label.bind("<Button-3>", self._on_right_click)
        self.bind("<Button-1>", self._on_left_click)
        self.bind("<Button-3>", self._on_right_click)

        self._update_display()

    def _update_display(self):
        weekday = self.current_date.strftime("%A")
        formatted = self.current_date.strftime("%d.%m.%Y")
        self.weekday_label.config(text=weekday)
        self.date_label.config(text=formatted)

    def _on_left_click(self, event=None):
        """Open date picker. When confirmed, update display and call on_date_change."""
        picker = DatePickerDialog(self.winfo_toplevel(), self.current_date)
        # Make the dialog modal relative to the main window
        picker.window.grab_set()
        self.winfo_toplevel().wait_window(picker.window)
        if getattr(picker, "result", None):
            self.current_date = picker.result
            self._update_display()
            if callable(self.on_date_change):
                try:
                    self.on_date_change(self.current_date)
                except Exception:
                    pass

    def _on_right_click(self, event=None):
        """Open the full detailed calendar (month view) in a new window."""
        DetailedCalendarWindow(self.winfo_toplevel(), self.event_manager, self.current_date)
