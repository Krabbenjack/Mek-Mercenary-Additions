"""
Event dialogs - GUI components for creating, editing, and managing events.

Provides:
- EventCreationDialog: Create new events with dropdown selections
- EventEditDialog: Edit existing events
- ManageEventsDialog: List, edit, and delete events for a specific day
- EventExecutionWindow: Display event details and execute with participants
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, Callable, List, Dict, Any

from .persistence import Event, EventType, RecurrenceType
from .participant_selector import get_participant_selector
from .injector import get_event_injector


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
        # Use first available event type as default
        first_event = list(EventType)[0]
        self.event_type_var = tk.StringVar(value=first_event.name)
        # Display event names (human readable) instead of numeric IDs
        event_type_combo = ttk.Combobox(
            self.window,
            textvariable=self.event_type_var,
            values=[et.name for et in EventType],
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
        event_type_name = self.event_type_var.get()
        recurrence_value = self.recurrence_var.get().lower()
        
        # Get EventType by name
        event_type = EventType[event_type_name]
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
        self.event_type_var = tk.StringVar(value=event.event_type.name)
        event_type_combo = ttk.Combobox(
            self.window,
            textvariable=self.event_type_var,
            values=[et.name for et in EventType],
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
        event_type_name = self.event_type_var.get()
        recurrence_value = self.recurrence_var.get().lower()
        
        event_type = EventType[event_type_name]
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


class EventExecutionWindow:
    """Window for displaying event details and executing with selected participants."""
    
    def __init__(self, parent, event: Event, execution_date: date, 
                 characters: Dict[str, Any], on_execute: Optional[Callable] = None):
        """
        Create an Event Execution Window.
        
        Args:
            parent: Parent tkinter widget (should be main window, not self.root)
            event: Event object to execute
            execution_date: Date of execution
            characters: Dictionary of Character objects keyed by ID
            on_execute: Optional callback to call after successful execution
        """
        self.event = event
        self.execution_date = execution_date
        self.characters = characters
        self.on_execute = on_execute
        
        # Get event details from injector
        injector = get_event_injector()
        is_valid, event_name = injector.validate_event_id(event.event_id)
        self.event_name = event_name if is_valid else "UNKNOWN"
        
        # Get participant selector
        selector = get_participant_selector()
        self.selector = selector
        
        # Check availability and get participants
        self.is_available, self.errors = selector.check_availability(event.event_id, characters)
        self.selected_participants = selector.select_participants(event.event_id, characters) if self.is_available else []
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Event Execution - {self.event_name}")
        self.window.geometry("600x500")
        self.window.grab_set()
        
        self._build_ui()
        
        self.window.transient(parent)
        self.window.focus()
    
    def _build_ui(self):
        """Build the UI for the event execution window."""
        # Header
        header_frame = tk.Frame(self.window, bg="#2c3e50", padx=10, pady=10)
        header_frame.pack(fill=tk.X)
        
        tk.Label(
            header_frame,
            text=f"Event: {self.event_name}",
            font=("Arial", 14, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(anchor=tk.W)
        
        tk.Label(
            header_frame,
            text=f"ID: {self.event.event_id}  |  Date: {self.execution_date.strftime('%Y-%m-%d')}",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # Main content area
        content_frame = tk.Frame(self.window, padx=15, pady=15)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Availability status
        status_frame = tk.Frame(content_frame)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        if self.is_available:
            tk.Label(
                status_frame,
                text="✓ Event Available",
                font=("Arial", 11, "bold"),
                fg="#27ae60"
            ).pack(anchor=tk.W)
        else:
            tk.Label(
                status_frame,
                text="✗ Event Not Available",
                font=("Arial", 11, "bold"),
                fg="#e74c3c"
            ).pack(anchor=tk.W)
            
            for error in self.errors:
                tk.Label(
                    status_frame,
                    text=f"  • {error}",
                    font=("Arial", 9),
                    fg="#c0392b"
                ).pack(anchor=tk.W, padx=(10, 0))
        
        # Participants section
        participants_label = tk.Label(
            content_frame,
            text="Selected Participants:",
            font=("Arial", 11, "bold")
        )
        participants_label.pack(anchor=tk.W, pady=(10, 5))
        
        # Participants listbox
        list_frame = tk.Frame(content_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.participants_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 10),
            height=10
        )
        self.participants_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.participants_listbox.yview)
        
        # Populate participants
        if self.selected_participants:
            for char_id in self.selected_participants:
                char = self.characters.get(char_id)
                if char:
                    display_text = f"{char.name}"
                    if char.callsign:
                        display_text += f" ({char.callsign})"
                    if char.profession:
                        display_text += f" - {char.profession}"
                    self.participants_listbox.insert(tk.END, display_text)
        else:
            self.participants_listbox.insert(tk.END, "No participants selected")
        
        # Button frame
        button_frame = tk.Frame(self.window, padx=15, pady=15)
        button_frame.pack(fill=tk.X)
        
        if self.is_available:
            tk.Button(
                button_frame,
                text="Start Event",
                command=self._execute_event,
                width=15,
                bg="#27ae60",
                fg="white",
                font=("Arial", 10, "bold")
            ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            width=15,
            font=("Arial", 10)
        ).pack(side=tk.RIGHT, padx=5)
    
    def _execute_event(self):
        """Execute the event and close the window."""
        try:
            # Execute via injector
            injector = get_event_injector()
            log = injector.execute_event(self.event.event_id, self.execution_date, self.characters)
            
            # Show success message
            if log.errors:
                messagebox.showwarning(
                    "Event Executed with Warnings",
                    f"Event '{self.event_name}' was executed but encountered issues:\n\n" +
                    "\n".join(log.errors)
                )
            else:
                messagebox.showinfo(
                    "Event Executed",
                    f"Event '{self.event_name}' executed successfully!\n\n" +
                    f"Participants: {len(self.selected_participants)}"
                )
            
            # Call the callback if provided
            if self.on_execute:
                self.on_execute(log)
            
            # Close window
            self.window.destroy()
        
        except Exception as e:
            messagebox.showerror(
                "Execution Error",
                f"Failed to execute event:\n{str(e)}"
            )
