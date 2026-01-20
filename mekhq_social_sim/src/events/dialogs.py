"""
Event dialogs - GUI components for creating, editing, and managing events.

Provides:
- EventCreationDialog: Create new events with dropdown selections
- EventEditDialog: Edit existing events
- ManageEventsDialog: List, edit, and delete events for a specific day
- EventExecutionWindow: Display event details and execute with participants
- EventResolveWindow: Display event resolution UI with participants and mechanics
"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from typing import Optional, Callable, List, Dict, Any
import logging

from .persistence import Event, EventType, RecurrenceType
from .participant_selector import get_participant_selector
from .injector import get_event_injector

# Import theme colors for resolve window
from ..ui_theme import RESOLVE_THEME

logger = logging.getLogger(__name__)


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
        
        # Check availability
        self.is_available, self.errors = selector.check_availability(event.event_id, characters)
        
        # Get eligible candidates and auto-selected participants
        if self.is_available:
            self.eligible_candidates = selector.get_eligible_candidates(
                event.event_id, characters, execution_date
            )
            self.auto_selected = selector.select_participants(
                event.event_id, characters, execution_date
            )
            # Start with auto-selected as current selection
            self.selected_participants = self.auto_selected.copy()
        else:
            self.eligible_candidates = []
            self.auto_selected = []
            self.selected_participants = []
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Event Execution - {self.event_name}")
        self.window.geometry("800x600")
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
        
        if self.is_available:
            # Two-list interface for participant selection
            participants_frame = tk.Frame(content_frame)
            participants_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            # Left side: Eligible Candidates
            left_frame = tk.Frame(participants_frame)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            tk.Label(
                left_frame,
                text="Eligible Candidates:",
                font=("Arial", 11, "bold")
            ).pack(anchor=tk.W, pady=(0, 5))
            
            left_list_frame = tk.Frame(left_frame)
            left_list_frame.pack(fill=tk.BOTH, expand=True)
            
            left_scrollbar = tk.Scrollbar(left_list_frame)
            left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.candidates_listbox = tk.Listbox(
                left_list_frame,
                yscrollcommand=left_scrollbar.set,
                font=("Arial", 10),
                selectmode=tk.SINGLE
            )
            self.candidates_listbox.pack(fill=tk.BOTH, expand=True)
            left_scrollbar.config(command=self.candidates_listbox.yview)
            
            # Bind click event to add to selected
            self.candidates_listbox.bind('<Double-Button-1>', self._on_candidate_double_click)
            
            # Right side: Selected Participants
            right_frame = tk.Frame(participants_frame)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            tk.Label(
                right_frame,
                text="Selected Participants:",
                font=("Arial", 11, "bold")
            ).pack(anchor=tk.W, pady=(0, 5))
            
            right_list_frame = tk.Frame(right_frame)
            right_list_frame.pack(fill=tk.BOTH, expand=True)
            
            right_scrollbar = tk.Scrollbar(right_list_frame)
            right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.selected_listbox = tk.Listbox(
                right_list_frame,
                yscrollcommand=right_scrollbar.set,
                font=("Arial", 10),
                selectmode=tk.SINGLE
            )
            self.selected_listbox.pack(fill=tk.BOTH, expand=True)
            right_scrollbar.config(command=self.selected_listbox.yview)
            
            # Bind click event to remove from selected
            self.selected_listbox.bind('<Double-Button-1>', self._on_selected_double_click)
            
            # Populate the lists
            self._refresh_lists()
            
            # Add instruction label
            instruction_label = tk.Label(
                content_frame,
                text="Double-click to add/remove participants",
                font=("Arial", 9, "italic"),
                fg="#7f8c8d"
            )
            instruction_label.pack(pady=(0, 10))
        
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
    
    def _get_character_display_text(self, char_id: str) -> str:
        """Get display text for a character."""
        char = self.characters.get(char_id)
        if not char:
            return f"Unknown ({char_id})"
        
        display_text = f"{char.name}"
        if char.callsign:
            display_text += f" ({char.callsign})"
        if char.profession:
            display_text += f" - {char.profession}"
        return display_text
    
    def _refresh_lists(self):
        """Refresh both listboxes based on current state."""
        # Clear both lists
        self.candidates_listbox.delete(0, tk.END)
        self.selected_listbox.delete(0, tk.END)
        
        # Populate candidates (those not in selected)
        for char_id in self.eligible_candidates:
            if char_id not in self.selected_participants:
                display_text = self._get_character_display_text(char_id)
                self.candidates_listbox.insert(tk.END, display_text)
        
        # Populate selected
        for char_id in self.selected_participants:
            display_text = self._get_character_display_text(char_id)
            self.selected_listbox.insert(tk.END, display_text)
        
        # If no candidates left, show message
        if self.candidates_listbox.size() == 0:
            self.candidates_listbox.insert(tk.END, "(All eligible candidates selected)")
    
    def _on_candidate_double_click(self, event):
        """Handle double-click on candidate to add to selected."""
        selection = self.candidates_listbox.curselection()
        if not selection:
            return
        
        # Get the index in candidates list
        idx = selection[0]
        
        # Find the corresponding character ID
        available_candidates = [
            cid for cid in self.eligible_candidates 
            if cid not in self.selected_participants
        ]
        
        if idx < len(available_candidates):
            char_id = available_candidates[idx]
            # Add to selected
            if char_id not in self.selected_participants:
                self.selected_participants.append(char_id)
                self._refresh_lists()
    
    def _on_selected_double_click(self, event):
        """Handle double-click on selected to remove from selected."""
        selection = self.selected_listbox.curselection()
        if not selection:
            return
        
        # Get the index in selected list
        idx = selection[0]
        
        if idx < len(self.selected_participants):
            char_id = self.selected_participants[idx]
            # Remove from selected
            self.selected_participants.remove(char_id)
            self._refresh_lists()
    
    def _execute_event(self):
        """Open Event Resolve Window with selected participants."""
        try:
            # Log final participant count (IDs excluded for privacy)
            logger.info(
                f"[EVENT_EXECUTION] Event {self.event.event_id}: "
                f"Opening Resolve Window with {len(self.selected_participants)} participants"
            )
            logger.debug(f"[EVENT_EXECUTION] Participant IDs: {self.selected_participants}")
            
            # Get environment and tone (placeholder values for now)
            # TODO: Load from event metadata when available
            environment = None
            tone = None
            
            # Close this window before opening resolve window
            parent = self.window.master
            self.window.destroy()
            
            # Open Event Resolve Window
            EventResolveWindow(
                parent=parent,
                event=self.event,
                execution_date=self.execution_date,
                participants=self.selected_participants,
                characters=self.characters,
                environment=environment,
                tone=tone,
                on_resolve=self.on_execute
            )
        
        except Exception as e:
            logger.error(f"[EVENT_EXECUTION] Failed to open Resolve Window: {e}")
            messagebox.showerror(
                "Resolve Window Error",
                f"Failed to open Event Resolve Window:\n{str(e)}"
            )


class EventResolveWindow:
    """
    Event Resolve Window - UI for event execution and mechanics.
    
    This is the main event resolution interface that shows:
    - Event metadata (name, ID, date, environment, tone)
    - Participants list with portraits
    - Mechanics panel (checks, rolls, effects)
    - Resolution controls
    
    Phase 1: UI-only, displays structure without real mechanics.
    """
    
    def __init__(self, parent, event: Event, execution_date: date, 
                 participants: List[str], characters: Dict[str, Any],
                 environment: Optional[str] = None, tone: Optional[str] = None,
                 on_resolve: Optional[Callable] = None):
        """
        Create Event Resolve Window.
        
        Args:
            parent: Parent tkinter widget
            event: Event object being resolved
            execution_date: Date of execution
            participants: List of character IDs participating
            characters: Dictionary of Character objects keyed by ID
            environment: Optional environment string (e.g., "SIMULATION", "LIVE_COMBAT")
            tone: Optional tone string (e.g., "formal", "informal")
            on_resolve: Optional callback after resolution
        """
        self.event = event
        self.execution_date = execution_date
        self.participants = participants
        self.characters = characters
        self.environment = environment or "—"
        self.tone = tone or "—"
        self.on_resolve = on_resolve
        
        # Get event name from injector
        injector = get_event_injector()
        is_valid, event_name = injector.validate_event_id(event.event_id)
        self.event_name = event_name if is_valid else "UNKNOWN"
        
        # Count participant types (for now, just total)
        self.primary_count = len(participants)  # Placeholder
        self.derived_count = 0  # Placeholder
        self.total_count = self.primary_count + self.derived_count
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Event Resolve - {self.event_name}")
        self.window.geometry("900x700")
        self.window.configure(bg=RESOLVE_THEME["window_bg"])
        self.window.grab_set()
        
        # Console logging
        logger.info(f"[RESOLVE_WINDOW] Opening event resolve window")
        logger.debug(f"[RESOLVE_WINDOW] Event: {event.event_id} - {self.event_name}")
        logger.debug(f"[RESOLVE_WINDOW] Date: {execution_date}, Participants: {len(participants)}")
        
        self._build_ui()
        
        self.window.transient(parent)
        self.window.focus()
    
    def _build_ui(self):
        """Build the complete UI layout."""
        # Header
        self._build_header()
        
        # Body (two columns)
        self._build_body()
        
        # Footer
        self._build_footer()
    
    def _build_header(self):
        """Build header with event metadata and chips."""
        header_frame = tk.Frame(
            self.window,
            bg=RESOLVE_THEME["header_bg"],
            highlightthickness=1,
            highlightbackground=RESOLVE_THEME["border"]
        )
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        # Left side: Event name and metadata
        left_frame = tk.Frame(header_frame, bg=RESOLVE_THEME["header_bg"])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Event name (large)
        name_label = tk.Label(
            left_frame,
            text=self.event_name,
            font=("Segoe UI", 16, "bold"),
            bg=RESOLVE_THEME["header_bg"],
            fg=RESOLVE_THEME["text_primary"]
        )
        name_label.pack(anchor=tk.W)
        
        # Event ID + Date (smaller)
        meta_text = f"Event ID: {self.event.event_id}  •  Date: {self.execution_date.strftime('%Y-%m-%d')}"
        meta_label = tk.Label(
            left_frame,
            text=meta_text,
            font=("Segoe UI", 10),
            bg=RESOLVE_THEME["header_bg"],
            fg=RESOLVE_THEME["text_secondary"]
        )
        meta_label.pack(anchor=tk.W, pady=(4, 0))
        
        # Right side: Environment and Tone chips
        right_frame = tk.Frame(header_frame, bg=RESOLVE_THEME["header_bg"])
        right_frame.pack(side=tk.RIGHT, padx=15, pady=15)
        
        # Environment chip
        env_chip = tk.Frame(
            right_frame,
            bg=RESOLVE_THEME["card_bg"],
            highlightthickness=1,
            highlightbackground=RESOLVE_THEME["border"]
        )
        env_chip.pack(side=tk.TOP, pady=(0, 4))
        
        tk.Label(
            env_chip,
            text=f"Environment: {self.environment}",
            font=("Segoe UI", 9),
            bg=RESOLVE_THEME["card_bg"],
            fg=RESOLVE_THEME["text_secondary"],
            padx=10,
            pady=4
        ).pack()
        
        # Tone chip
        tone_chip = tk.Frame(
            right_frame,
            bg=RESOLVE_THEME["card_bg"],
            highlightthickness=1,
            highlightbackground=RESOLVE_THEME["border"]
        )
        tone_chip.pack(side=tk.TOP)
        
        tk.Label(
            tone_chip,
            text=f"Tone: {self.tone}",
            font=("Segoe UI", 9),
            bg=RESOLVE_THEME["card_bg"],
            fg=RESOLVE_THEME["text_secondary"],
            padx=10,
            pady=4
        ).pack()
    
    def _build_body(self):
        """Build body with two columns: participants (left) and mechanics (right)."""
        body_frame = tk.Frame(self.window, bg=RESOLVE_THEME["window_bg"])
        body_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Left panel: Participants
        self._build_participants_panel(body_frame)
        
        # Right panel: Mechanics
        self._build_mechanics_panel(body_frame)
    
    def _build_participants_panel(self, parent):
        """Build left panel with participants list."""
        panel = tk.Frame(
            parent,
            bg=RESOLVE_THEME["panel_bg"],
            highlightthickness=1,
            highlightbackground=RESOLVE_THEME["border"]
        )
        panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))
        
        # Header with title and counts
        header = tk.Frame(panel, bg=RESOLVE_THEME["panel_bg"])
        header.pack(fill=tk.X, padx=12, pady=10)
        
        tk.Label(
            header,
            text="Participants",
            font=("Segoe UI", 12, "bold"),
            bg=RESOLVE_THEME["panel_bg"],
            fg=RESOLVE_THEME["text_primary"]
        ).pack(anchor=tk.W)
        
        # Summary counts
        summary_text = f"Primary: {self.primary_count} • Derived: {self.derived_count} • Total: {self.total_count}"
        tk.Label(
            header,
            text=summary_text,
            font=("Segoe UI", 9),
            bg=RESOLVE_THEME["panel_bg"],
            fg=RESOLVE_THEME["text_muted"]
        ).pack(anchor=tk.W, pady=(4, 0))
        
        # Scrollable list container
        list_container = tk.Frame(panel, bg=RESOLVE_THEME["panel_bg"])
        list_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        
        # Canvas for scrolling
        canvas = tk.Canvas(
            list_container,
            bg=RESOLVE_THEME["panel_bg"],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(list_container, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=RESOLVE_THEME["panel_bg"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate participant rows
        for char_id in self.participants:
            self._create_participant_row(scrollable_frame, char_id)
        
        # Store for later interaction
        self.participant_list_frame = scrollable_frame
    
    def _create_participant_row(self, parent, char_id: str):
        """Create a single participant row with portrait, name, role, rank."""
        char = self.characters.get(char_id)
        if not char:
            return
        
        # Row container (card)
        row = tk.Frame(
            parent,
            bg=RESOLVE_THEME["card_bg"],
            highlightthickness=1,
            highlightbackground=RESOLVE_THEME["border"]
        )
        row.pack(fill=tk.X, padx=4, pady=3)
        
        # Portrait placeholder (left side, 40x40)
        portrait_frame = tk.Frame(
            row,
            width=40,
            height=40,
            bg=RESOLVE_THEME["border"]
        )
        portrait_frame.pack(side=tk.LEFT, padx=8, pady=8)
        portrait_frame.pack_propagate(False)
        
        # Portrait label (could load actual image later)
        tk.Label(
            portrait_frame,
            text="?",
            font=("Segoe UI", 16, "bold"),
            bg=RESOLVE_THEME["border"],
            fg=RESOLVE_THEME["text_muted"]
        ).pack(expand=True)
        
        # Text container (right side)
        text_container = tk.Frame(row, bg=RESOLVE_THEME["card_bg"])
        text_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)
        
        # Name (primary text)
        name_lbl = tk.Label(
            text_container,
            text=char.name,
            font=("Segoe UI", 10, "bold"),
            bg=RESOLVE_THEME["card_bg"],
            fg=RESOLVE_THEME["text_primary"],
            anchor=tk.W
        )
        name_lbl.pack(anchor=tk.W)
        
        # Role + Rank (secondary text)
        role_parts = [char.profession, char.rank_name]
        role_text = " • ".join(filter(None, role_parts)) or "Unknown Role"
        
        role_lbl = tk.Label(
            text_container,
            text=role_text,
            font=("Segoe UI", 9),
            bg=RESOLVE_THEME["card_bg"],
            fg=RESOLVE_THEME["text_secondary"],
            anchor=tk.W
        )
        role_lbl.pack(anchor=tk.W, pady=(2, 0))
        
        # Hover effect (defined after labels are created)
        def on_enter(e):
            row.configure(bg=RESOLVE_THEME["card_hover"])
            name_lbl.configure(bg=RESOLVE_THEME["card_hover"])
            role_lbl.configure(bg=RESOLVE_THEME["card_hover"])
        
        def on_leave(e):
            row.configure(bg=RESOLVE_THEME["card_bg"])
            name_lbl.configure(bg=RESOLVE_THEME["card_bg"])
            role_lbl.configure(bg=RESOLVE_THEME["card_bg"])
        
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        name_lbl.bind("<Enter>", on_enter)
        name_lbl.bind("<Leave>", on_leave)
        role_lbl.bind("<Enter>", on_enter)
        role_lbl.bind("<Leave>", on_leave)
    
    def _build_mechanics_panel(self, parent):
        """Build right panel with mechanics placeholder."""
        panel = tk.Frame(
            parent,
            bg=RESOLVE_THEME["panel_bg"],
            highlightthickness=1,
            highlightbackground=RESOLVE_THEME["border"]
        )
        panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 0))
        
        # Header
        header = tk.Frame(panel, bg=RESOLVE_THEME["panel_bg"])
        header.pack(fill=tk.X, padx=12, pady=10)
        
        tk.Label(
            header,
            text="Checks & Effects",
            font=("Segoe UI", 12, "bold"),
            bg=RESOLVE_THEME["panel_bg"],
            fg=RESOLVE_THEME["text_primary"]
        ).pack(anchor=tk.W)
        
        # Placeholder content
        placeholder_frame = tk.Frame(panel, bg=RESOLVE_THEME["panel_bg"])
        placeholder_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=20)
        
        placeholder_card = tk.Frame(
            placeholder_frame,
            bg=RESOLVE_THEME["card_bg"],
            highlightthickness=1,
            highlightbackground=RESOLVE_THEME["border"]
        )
        placeholder_card.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        
        tk.Label(
            placeholder_card,
            text="No mechanics implemented yet.\nThis panel will show checks, rolls and effects.",
            font=("Segoe UI", 10),
            bg=RESOLVE_THEME["card_bg"],
            fg=RESOLVE_THEME["text_muted"],
            justify=tk.CENTER
        ).pack(expand=True, pady=40)
    
    def _build_footer(self):
        """Build footer with action buttons."""
        footer_frame = tk.Frame(
            self.window,
            bg=RESOLVE_THEME["window_bg"]
        )
        footer_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        # Right-aligned button container
        button_container = tk.Frame(footer_frame, bg=RESOLVE_THEME["window_bg"])
        button_container.pack(side=tk.RIGHT)
        
        # Close button (secondary)
        close_btn = tk.Frame(
            button_container,
            bg=RESOLVE_THEME["btn_secondary_bg"],
            highlightthickness=1,
            highlightbackground=RESOLVE_THEME["btn_secondary_border"]
        )
        close_btn.pack(side=tk.RIGHT, padx=(8, 0))
        
        close_lbl = tk.Label(
            close_btn,
            text="Close",
            font=("Segoe UI", 10),
            bg=RESOLVE_THEME["btn_secondary_bg"],
            fg=RESOLVE_THEME["btn_secondary_text"],
            padx=20,
            pady=8,
            cursor="hand2"
        )
        close_lbl.pack()
        
        def on_close_click(e):
            logger.info(f"[RESOLVE_WINDOW] Close button clicked")
            self.window.destroy()
        
        def on_close_enter(e):
            close_btn.configure(bg=RESOLVE_THEME["btn_secondary_hover"])
            close_lbl.configure(bg=RESOLVE_THEME["btn_secondary_hover"])
        
        def on_close_leave(e):
            close_btn.configure(bg=RESOLVE_THEME["btn_secondary_bg"])
            close_lbl.configure(bg=RESOLVE_THEME["btn_secondary_bg"])
        
        close_lbl.bind("<Button-1>", on_close_click)
        close_btn.bind("<Enter>", on_close_enter)
        close_btn.bind("<Leave>", on_close_leave)
        close_lbl.bind("<Enter>", on_close_enter)
        close_lbl.bind("<Leave>", on_close_leave)
        
        # Resolve Event button (primary)
        resolve_btn = tk.Frame(
            button_container,
            bg=RESOLVE_THEME["btn_primary_bg"],
            highlightthickness=0
        )
        resolve_btn.pack(side=tk.RIGHT)
        
        resolve_lbl = tk.Label(
            resolve_btn,
            text="Resolve Event",
            font=("Segoe UI", 10, "bold"),
            bg=RESOLVE_THEME["btn_primary_bg"],
            fg=RESOLVE_THEME["btn_primary_text"],
            padx=20,
            pady=8,
            cursor="hand2"
        )
        resolve_lbl.pack()
        
        def on_resolve_click(e):
            logger.info(f"[RESOLVE_WINDOW] Resolve Event button clicked")
            # Placeholder action
            messagebox.showinfo(
                "Resolve Event",
                "Event resolution mechanics not yet implemented.\nThis is a placeholder action."
            )
        
        def on_resolve_enter(e):
            resolve_btn.configure(bg=RESOLVE_THEME["btn_primary_hover"])
            resolve_lbl.configure(bg=RESOLVE_THEME["btn_primary_hover"])
        
        def on_resolve_leave(e):
            resolve_btn.configure(bg=RESOLVE_THEME["btn_primary_bg"])
            resolve_lbl.configure(bg=RESOLVE_THEME["btn_primary_bg"])
        
        resolve_lbl.bind("<Button-1>", on_resolve_click)
        resolve_btn.bind("<Enter>", on_resolve_enter)
        resolve_btn.bind("<Leave>", on_resolve_leave)
        resolve_lbl.bind("<Enter>", on_resolve_enter)
        resolve_lbl.bind("<Leave>", on_resolve_leave)

