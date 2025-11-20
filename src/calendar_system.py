"""
Calendar System with GUI - Tkinter Implementation
A modular, extensible calendar with events/appointments management.

This module provides:
- Main calendar window with date display
- Date picker (left-click on date display)
- Detailed calendar view (right-click on date display)
- Event creation with recurrence options (DAILY, WEEKLY, MONTHLY, YEARLY, ONCE)
- Event storage and retrieval with recurrence calculation

Run: python src/calendar_system.py
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from enum import Enum
from typing import List
import calendar as calendar_module


# ============================================================================
# BUSINESS LOGIC - DATA MODEL & EVENT HANDLING
# ============================================================================

class RecurrenceType(Enum):
    """Enum for event recurrence types."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Event:
    """
    Represents a single event/appointment.

    Attributes:
        id: Unique identifier (incrementing counter)
        title: Event name/description
        start_date: datetime.date object
        recurrence_type: RecurrenceType enum
    """

    _counter = 0

    def __init__(self, title: str, start_date, recurrence_type: RecurrenceType):
        Event._counter += 1
        self.id = Event._counter
        self.title = title
        self.start_date = start_date
        self.recurrence_type = recurrence_type

    def __repr__(self):
        return f"Event(id={self.id}, title='{self.title}', date={self.start_date}, recurrence={self.recurrence_type.value})"


class EventManager:
    """
    Business logic for managing events.
    Handles storage, retrieval, and recurrence calculation.
    """

    def __init__(self):
        """Initialize empty event storage (in-memory)."""
        self.events: List[Event] = []

    def add_event(self, title: str, start_date, recurrence_type: RecurrenceType) -> Event:
        """
        Add a new event to storage.

        Args:
            title: Event description
            start_date: datetime.date object
            recurrence_type: RecurrenceType enum value

        Returns:
            The created Event object
        """
        event = Event(title, start_date, recurrence_type)
        self.events.append(event)
        return event

    def remove_event(self, event_id: int) -> bool:
        """Remove an event by ID."""
        for i, event in enumerate(self.events):
            if event.id == event_id:
                self.events.pop(i)
                return True
        return False

    def get_events_for_date(self, target_date) -> List[Event]:
        """
        Get all events active on a specific date (including recurring ones).

        Args:
            target_date: datetime.date object

        Returns:
            List of Event objects that occur on target_date
        """
        active_events = []
        for event in self.events:
            if self._event_occurs_on_date(event, target_date):
                active_events.append(event)
        return active_events

    def _event_occurs_on_date(self, event: Event, target_date) -> bool:
        """
        Check if a specific event occurs on the target date based on recurrence rules.

        Recurrence logic:
        - ONCE: only on start_date
        - DAILY: every day on/after start_date
        - WEEKLY: same weekday every 7 days from start_date
        - MONTHLY: same day-of-month if day exists (simple check: day matches)
        - YEARLY: same month and day every year on/after start_date

        Note: This is intentionally simple and can be extended (e.g. RRULE support).
        """
        if target_date < event.start_date:
            return False

        r = event.recurrence_type
        if r == RecurrenceType.ONCE:
            return target_date == event.start_date
        if r == RecurrenceType.DAILY:
            return True
        if r == RecurrenceType.WEEKLY:
            return (target_date - event.start_date).days % 7 == 0
        if r == RecurrenceType.MONTHLY:
            # Occurs if day-of-month matches. Does not attempt to shift for months without the day.
            return target_date.day == event.start_date.day and target_date >= event.start_date
        if r == RecurrenceType.YEARLY:
            return (target_date.month == event.start_date.month and
                    target_date.day == event.start_date.day and
                    target_date >= event.start_date)
        return False

    def get_all_events(self) -> List[Event]:
        """Return all stored events (shallow copy)."""
        return self.events.copy()

    def save_events(self, filepath: str) -> None:
        """
        STUB: Save events to persistent storage (file/database).

        Where to implement persistence:
        - JSON serialization
        - SQLite database
        - CSV export
        """
        # TODO: Implement file/database persistence
        print(f"[SAVE] Would save {len(self.events)} events to {filepath}")

    def load_events(self, filepath: str) -> None:
        """STUB: Load events from persistent storage."""
        # TODO: Implement file/database loading
        print(f"[LOAD] Would load events from {filepath}")


# ============================================================================
# UI LOGIC - TKINTER WIDGETS & WINDOWS
# ============================================================================

class DatePickerDialog:
    """
    Simple date picker dialog.
    Allows user to select a date via spinboxes.
    """

    def __init__(self, parent, current_date=None):
        self.result = None
        if current_date is None:
            current_date = datetime.now().date()

        self.window = tk.Toplevel(parent)
        self.window.title("Select Date")
        self.window.geometry("300x150")
        self.window.grab_set()

        tk.Label(self.window, text="Day:").grid(row=0, column=0, padx=5, pady=5)
        self.day_var = tk.StringVar(value=f"{current_date.day:02d}")
        day_spinbox = ttk.Spinbox(self.window, from_=1, to=31, textvariable=self.day_var, width=5)
        day_spinbox.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.window, text="Month:").grid(row=1, column=0, padx=5, pady=5)
        self.month_var = tk.StringVar(value=f"{current_date.month:02d}")
        month_spinbox = ttk.Spinbox(self.window, from_=1, to=12, textvariable=self.month_var, width=5)
        month_spinbox.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.window, text="Year:").grid(row=2, column=0, padx=5, pady=5)
        self.year_var = tk.StringVar(value=str(current_date.year))
        year_spinbox = ttk.Spinbox(self.window, from_=1900, to=2100, textvariable=self.year_var, width=7)
        year_spinbox.grid(row=2, column=1, padx=5, pady=5)

        button_frame = tk.Frame(self.window)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        tk.Button(button_frame, text="OK", command=self._on_ok, width=8).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.window.destroy, width=8).pack(side=tk.LEFT, padx=5)

        self.window.transient(parent)
        self.window.focus()

    def _on_ok(self):
        try:
            day = int(self.day_var.get())
            month = int(self.month_var.get())
            year = int(self.year_var.get())
            self.result = datetime(year, month, day).date()
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Invalid Date", f"Please enter a valid date.\n{str(e)}")


class EventCreationDialog:
    """Dialog for creating a new event with recurrence selection."""

    def __init__(self, parent, selected_date):
        self.result = None  # (title, recurrence_type)
        self.selected_date = selected_date

        self.window = tk.Toplevel(parent)
        self.window.title("Create Event")
        self.window.geometry("350x220")
        self.window.grab_set()

        date_str = selected_date.strftime("%A, %d.%m.%Y")
        tk.Label(self.window, text=f"Date: {date_str}", font=("Arial", 10, "bold")).pack(pady=8)

        tk.Label(self.window, text="Event Title:").pack(anchor=tk.W, padx=10)
        self.title_entry = tk.Entry(self.window, width=40)
        self.title_entry.pack(padx=10, pady=5)
        self.title_entry.focus()

        tk.Label(self.window, text="Recurrence:").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.recurrence_var = tk.StringVar(value=RecurrenceType.ONCE.value)
        recurrence_frame = tk.Frame(self.window)
        recurrence_frame.pack(padx=10, pady=5)

        for recurrence_type in RecurrenceType:
            tk.Radiobutton(recurrence_frame,
                           text=recurrence_type.value.capitalize(),
                           variable=self.recurrence_var,
                           value=recurrence_type.value).pack(anchor=tk.W)

        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        tk.Button(button_frame, text="Create", command=self._on_create, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.window.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def _on_create(self):
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Empty Title", "Please enter an event title.")
            return
        recurrence_value = self.recurrence_var.get()
        recurrence_type = RecurrenceType(recurrence_value)
        self.result = (title, recurrence_type)
        self.window.destroy()


class DetailedCalendarWindow:
    """
    Detailed calendar view with month navigation and event display.
    """

    def __init__(self, parent, event_manager: EventManager, current_date=None):
        self.event_manager = event_manager
        self.current_date = current_date or datetime.now().date()
        self.selected_date = self.current_date

        self.window = tk.Toplevel(parent)
        self.window.title("Calendar View")
        self.window.geometry("700x600")

        self._create_navigation()
        self._create_calendar_grid()
        self._create_events_panel()

        self._refresh_calendar()

    def _create_navigation(self):
        nav_frame = tk.Frame(self.window)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(nav_frame, text="<< Previous", command=self._prev_month, width=12).pack(side=tk.LEFT, padx=5)
        self.month_label = tk.Label(nav_frame, text="", font=("Arial", 14, "bold"))
        self.month_label.pack(side=tk.LEFT, expand=True)
        tk.Button(nav_frame, text="Next >>", command=self._next_month, width=12).pack(side=tk.LEFT, padx=5)

    def _create_calendar_grid(self):
        self.calendar_frame = tk.Frame(self.window)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for col, day in enumerate(days):
            tk.Label(self.calendar_frame, text=day, font=("Arial", 10, "bold"),
                     bg="lightgray", padx=5, pady=5).grid(row=0, column=col, sticky="nsew")

        self.day_buttons = {}
        for row in range(1, 7):
            for col in range(7):
                btn = tk.Button(self.calendar_frame, text="", font=("Arial", 10),
                                width=8, height=3, command=lambda r=row, c=col: self._on_day_click(r, c))
                btn.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
                self.day_buttons[(row, col)] = btn

        for i in range(7):
            self.calendar_frame.grid_columnconfigure(i, weight=1)
        for i in range(7):
            self.calendar_frame.grid_rowconfigure(i, weight=1)

    def _create_events_panel(self):
        events_frame = tk.LabelFrame(self.window, text="Events for Selected Date", padx=10, pady=10)
        events_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(events_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.events_listbox = tk.Listbox(events_frame, yscrollcommand=scrollbar.set, height=6)
        self.events_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.events_listbox.yview)

        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=5)
        tk.Button(button_frame, text="Add Event", command=self._on_add_event, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove Event", command=self._on_remove_event, width=12).pack(side=tk.LEFT, padx=5)

    def _prev_month(self):
        if self.current_date.month == 1:
            self.current_date = datetime(self.current_date.year - 1, 12, 1).date()
        else:
            self.current_date = datetime(self.current_date.year, self.current_date.month - 1, 1).date()
        self._refresh_calendar()

    def _next_month(self):
        if self.current_date.month == 12:
            self.current_date = datetime(self.current_date.year + 1, 1, 1).date()
        else:
            self.current_date = datetime(self.current_date.year, self.current_date.month + 1, 1).date()
        self._refresh_calendar()

    def _refresh_calendar(self):
        year = self.current_date.year
        month = self.current_date.month
        self.month_label.config(text=datetime(year, month, 1).strftime("%B %Y"))

        cal = calendar_module.monthcalendar(year, month)

        for (row, col), btn in self.day_buttons.items():
            btn.config(text="", bg="white", fg="black", state=tk.NORMAL)

        for week_num, week in enumerate(cal):
            for day_num, day in enumerate(week):
                if day == 0:
                    continue
                row = week_num + 1
                col = day_num
                btn = self.day_buttons[(row, col)]
                date_obj = datetime(year, month, day).date()
                events = self.event_manager.get_events_for_date(date_obj)
                display_text = str(day)
                if events:
                    display_text += f"\n({len(events)} event{'s' if len(events) > 1 else ''})"
                    btn.config(bg="lightblue")
                btn.config(text=display_text)
        self._update_events_display()

    def _on_day_click(self, row, col):
        btn = self.day_buttons[(row, col)]
        day_text = btn.cget("text").split('\n')[0]
        if day_text:
            try:
                day = int(day_text)
                self.selected_date = datetime(self.current_date.year, self.current_date.month, day).date()
                self._update_events_display()
            except ValueError:
                pass

    def _update_events_display(self):
        self.events_listbox.delete(0, tk.END)
        events = self.event_manager.get_events_for_date(self.selected_date)
        for event in events:
            self.events_listbox.insert(tk.END, f"{event.title} ({event.recurrence_type.value})")

    def _on_add_event(self):
        dialog = EventCreationDialog(self.window, self.selected_date)
        self.window.wait_window(dialog.window)
        if dialog.result:
            title, recurrence_type = dialog.result
            self.event_manager.add_event(title, self.selected_date, recurrence_type)
            self._refresh_calendar()

    def _on_remove_event(self):
        selection = self.events_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an event to remove.")
            return
        events = self.event_manager.get_events_for_date(self.selected_date)
        event_to_remove = events[selection[0]]
        self.event_manager.remove_event(event_to_remove.id)
        self._refresh_calendar()


class MainCalendarWindow:
    """
    Main calendar application window.
    - Date display with weekday and formatted date (DD.MM.YYYY)
    - Left-click opens DatePickerDialog (<Button-1>)
    - Right-click opens DetailedCalendarWindow (<Button-3>)
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Calendar System")
        self.root.geometry("500x300")

        # business logic component
        self.event_manager = EventManager()

        # current date state
        self.current_date = datetime.now().date()

        # build UI
        self._create_widgets()
        self._bind_mouse_events()

    def _create_widgets(self):
        title = tk.Label(self.root, text="Calendar System", font=("Arial", 18, "bold"))
        title.pack(pady=20)

        self.date_frame = tk.Frame(self.root, bg="lightblue", padx=20, pady=20, relief=tk.RAISED, bd=2)
        self.date_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.weekday_label = tk.Label(self.date_frame, text="", font=("Arial", 16), bg="lightblue", fg="darkblue")
        self.weekday_label.pack(pady=6)

        self.date_label = tk.Label(self.date_frame, text="", font=("Arial", 24, "bold"), bg="lightblue", fg="darkblue")
        self.date_label.pack(pady=6)

        instruction_text = ("Left-click: Open date picker\nRight-click: Open detailed calendar view")
        instruction = tk.Label(self.root, text=instruction_text, font=("Arial", 10), fg="gray", justify=tk.CENTER)
        instruction.pack(pady=8)

        self._update_date_display()

    def _bind_mouse_events(self):
        # Left-click is <Button-1>, right-click is <Button-3>
        self.date_frame.bind("<Button-1>", self._on_date_left_click)
        self.date_frame.bind("<Button-3>", self._on_date_right_click)
        self.weekday_label.bind("<Button-1>", self._on_date_left_click)
        self.weekday_label.bind("<Button-3>", self._on_date_right_click)
        self.date_label.bind("<Button-1>", self._on_date_left_click)
        self.date_label.bind("<Button-3>", self._on_date_right_click)

    def _update_date_display(self):
        weekday_name = self.current_date.strftime("%A")
        formatted_date = self.current_date.strftime("%d.%m.%Y")
        self.weekday_label.config(text=weekday_name)
        self.date_label.config(text=formatted_date)

    def _on_date_left_click(self, event):
        # Open date picker dialog; on confirm update main date display
        picker = DatePickerDialog(self.root, self.current_date)
        self.root.wait_window(picker.window)
        if picker.result:
            self.current_date = picker.result
            self._update_date_display()

    def _on_date_right_click(self, event):
        # Open detailed calendar window showing current_date's month
        DetailedCalendarWindow(self.root, self.event_manager, self.current_date)


# ============================================================================
# MAIN ENTRY POINT & CUSTOMIZATION GUIDE
# ============================================================================

def main():
    """
    Main entry point for the calendar application.

    Look & feel:
    - Change color and font values in widget creation (bg=, fg=, font=(...))
    Persistence:
    - Implement EventManager.save_events/load_events with JSON/SQLite/CSV
    Embedding:
    - Import EventManager or MainCalendarWindow into other modules and integrate into your app's Tk root.
    """
    root = tk.Tk()
    app = MainCalendarWindow(root)

    # sample events for demonstration
    today = datetime.now().date()
    app.event_manager.add_event("Team Meeting", today, RecurrenceType.WEEKLY)
    app.event_manager.add_event("Dentist Appointment", today + timedelta(days=5), RecurrenceType.ONCE)
    # birthday example (replace year if necessary)
    try:
        birthday = today.replace(month=12, day=25)
    except ValueError:
        birthday = today
    app.event_manager.add_event("Birthday Reminder", birthday, RecurrenceType.YEARLY)

    root.mainloop()


if __name__ == "__main__":
    main()
