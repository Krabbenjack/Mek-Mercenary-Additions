"""
Event dialogs - GUI components for creating, editing, and managing events.

Provides:
- EventCreationDialog: Create new events with dropdown selections
- EventEditDialog: Edit existing events
- ManageEventsDialog: List, edit, and delete events for a specific day
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, Callable, List

from .persistence import Event, EventType, RecurrenceType


class EventCreationDialog:
    """Dialog for creating a new event with dropdown selections."""

    def __init__(self, parent, selected_date: date):
        self.result = None  # (event_type, recurrence_type)
        self.selected_date = selected_date

        self.window = tk.Toplevel(parent)
        self.window.title("Create Event")
        self.window.geometry("400x250")
        self.window.grab_set()

        date_str = selected_date.strftime("%A, %d.%m.%Y")
        tk.Label(self.window, text=f"Date: {date_str}", font=("Arial", 10, "bold")).pack(pady=8)

        # Event Type dropdown
        tk.Label(self.window, text="Event Type:").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.event_type_var = tk.StringVar(value=EventType.FIELD_TRAINING.value)
        event_type_combo = ttk.Combobox(
            self.window,
            textvariable=self.event_type_var,
            values=[et.value for et in EventType],
            state="readonly",
            width=35
        )
        event_type_combo.pack(padx=10, pady=5)

        # Recurrence dropdown
        tk.Label(self.window, text="Recurrence:").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.recurrence_var = tk.StringVar(value=RecurrenceType.ONCE.value)
        recurrence_combo = ttk.Combobox(
            self.window,
            textvariable=self.recurrence_var,
            values=[rt.value.capitalize() for rt in RecurrenceType],
            state="readonly",
            width=35
        )
        recurrence_combo.pack(padx=10, pady=5)

        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=15)
        tk.Button(button_frame, text="Create", command=self._on_create, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.window.destroy, width=10).pack(side=tk.LEFT, padx=5)

        self.window.transient(parent)
        self.window.focus()

    def _on_create(self):
        event_type_value = self.event_type_var.get()
        recurrence_value = self.recurrence_var.get().lower()
        
        event_type = EventType(event_type_value)
        recurrence_type = RecurrenceType(recurrence_value)
        
        self.result = (event_type, recurrence_type)
        self.window.destroy()


class EventEditDialog:
    """Dialog for editing an existing event."""

    def __init__(self, parent, event: Event):
        self.result = None  # (event_type, start_date, recurrence_type)
        self.event = event

        self.window = tk.Toplevel(parent)
        self.window.title("Edit Event")
        self.window.geometry("400x250")
        self.window.grab_set()

        tk.Label(self.window, text=f"Editing Event ID: {event.id}", font=("Arial", 10, "bold")).pack(pady=8)

        date_str = event.start_date.strftime("%A, %d.%m.%Y")
        tk.Label(self.window, text=f"Date: {date_str}", font=("Arial", 10)).pack(pady=4)

        # Event Type dropdown
        tk.Label(self.window, text="Event Type:").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.event_type_var = tk.StringVar(value=event.event_type.value)
        event_type_combo = ttk.Combobox(
            self.window,
            textvariable=self.event_type_var,
            values=[et.value for et in EventType],
            state="readonly",
            width=35
        )
        event_type_combo.pack(padx=10, pady=5)

        # Recurrence dropdown
        tk.Label(self.window, text="Recurrence:").pack(anchor=tk.W, padx=10, pady=(8, 0))
        self.recurrence_var = tk.StringVar(value=event.recurrence_type.value.capitalize())
        recurrence_combo = ttk.Combobox(
            self.window,
            textvariable=self.recurrence_var,
            values=[rt.value.capitalize() for rt in RecurrenceType],
            state="readonly",
            width=35
        )
        recurrence_combo.pack(padx=10, pady=5)

        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=15)
        tk.Button(button_frame, text="Save", command=self._on_save, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Cancel", command=self.window.destroy, width=10).pack(side=tk.LEFT, padx=5)

        self.window.transient(parent)
        self.window.focus()

    def _on_save(self):
        event_type_value = self.event_type_var.get()
        recurrence_value = self.recurrence_var.get().lower()
        
        event_type = EventType(event_type_value)
        recurrence_type = RecurrenceType(recurrence_value)
        
        self.result = (event_type, self.event.start_date, recurrence_type)
        self.window.destroy()


class ManageEventsDialog:
    """Dialog for listing, editing, and deleting events for a specific day."""

    def __init__(self, parent, selected_date: date, events: List[Event], 
                 on_edit: Callable[[Event], None], on_delete: Callable[[Event], None]):
        """
        Args:
            parent: Parent tkinter widget
            selected_date: Date for which to manage events
            events: List of events occurring on this date
            on_edit: Callback function to edit an event
            on_delete: Callback function to delete an event
        """
        self.selected_date = selected_date
        self.events = events
        self.on_edit = on_edit
        self.on_delete = on_delete

        self.window = tk.Toplevel(parent)
        self.window.title("Manage Events")
        self.window.geometry("500x400")
        self.window.grab_set()

        date_str = selected_date.strftime("%A, %d.%m.%Y")
        tk.Label(self.window, text=f"Events for: {date_str}", font=("Arial", 12, "bold")).pack(pady=10)

        # Events listbox
        list_frame = tk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.events_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Arial", 10))
        self.events_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.events_listbox.yview)

        self._populate_list()

        # Buttons
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Edit", command=self._on_edit_clicked, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Delete", command=self._on_delete_clicked, width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=self.window.destroy, width=12).pack(side=tk.LEFT, padx=5)

        self.window.transient(parent)
        self.window.focus()

    def _populate_list(self):
        self.events_listbox.delete(0, tk.END)
        if not self.events:
            self.events_listbox.insert(tk.END, "No events for this day")
        else:
            for event in self.events:
                display_text = f"{event.title} ({event.recurrence_type.value}) [ID: {event.id}]"
                self.events_listbox.insert(tk.END, display_text)

    def _on_edit_clicked(self):
        selection = self.events_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an event to edit.")
            return
        
        event = self.events[selection[0]]
        self.on_edit(event)
        self.window.destroy()

    def _on_delete_clicked(self):
        selection = self.events_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an event to delete.")
            return
        
        event = self.events[selection[0]]
        
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete this event?\n\n{event.title}\n({event.recurrence_type.value})"
        )
        
        if confirm:
            self.on_delete(event)
            self.window.destroy()
