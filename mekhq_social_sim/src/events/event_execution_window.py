"""
Event Execution Window - Minimal UI for participant selection and event execution.

Opens before an event is executed to show:
- Event metadata (name, date, ID)
- Available characters for selection
- Selected participants
- Start Event button

Design: Functional, not polished. Uses existing theme styles where possible.
"""
import tkinter as tk
from tkinter import ttk
from datetime import date
from typing import List, Optional, Callable, Any


class EventExecutionWindow:
    """
    Minimal dialog for event execution with participant selection.
    
    Opens before event execution to allow reviewing/modifying participants.
    """
    
    def __init__(self, parent, event_id: int, event_name: str, execution_date: date,
                 available_characters: List[Any], suggested_participants: List[Any],
                 on_start: Callable[[List[Any]], None]):
        """
        Initialize the event execution window.
        
        Args:
            parent: Parent tkinter widget
            event_id: Event ID from eventlist.json
            event_name: Human-readable event name
            execution_date: Date of event execution
            available_characters: List of all available Character objects
            suggested_participants: List of suggested Character objects (from selection engine)
            on_start: Callback function(selected_participants) when Start Event is clicked
        """
        self.parent = parent
        self.event_id = event_id
        self.event_name = event_name
        self.execution_date = execution_date
        self.available_characters = available_characters
        self.on_start = on_start
        
        # Track selected participants
        self.selected_participants: List[Any] = list(suggested_participants)
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Event Execution")
        self.window.geometry("800x600")
        self.window.grab_set()
        
        # Create UI
        self._create_header()
        self._create_character_lists()
        self._create_buttons()
        
        # Center window
        self.window.transient(parent)
        self.window.focus()
    
    def _create_header(self):
        """Create header section with event metadata."""
        header_frame = tk.Frame(self.window, bg="lightgray", padx=10, pady=10)
        header_frame.pack(fill=tk.X)
        
        # Event name (bold, larger)
        name_label = tk.Label(
            header_frame,
            text=self.event_name,
            font=("Arial", 14, "bold"),
            bg="lightgray"
        )
        name_label.pack(anchor=tk.W)
        
        # Event date
        date_str = self.execution_date.strftime("%A, %d.%m.%Y")
        date_label = tk.Label(
            header_frame,
            text=f"Date: {date_str}",
            font=("Arial", 10),
            bg="lightgray"
        )
        date_label.pack(anchor=tk.W)
        
        # Event ID
        id_label = tk.Label(
            header_frame,
            text=f"Event ID: {self.event_id}",
            font=("Arial", 9),
            fg="gray",
            bg="lightgray"
        )
        id_label.pack(anchor=tk.W)
    
    def _create_character_lists(self):
        """Create the two-column layout with character lists."""
        lists_frame = tk.Frame(self.window)
        lists_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure columns
        lists_frame.columnconfigure(0, weight=1)
        lists_frame.columnconfigure(1, weight=1)
        lists_frame.rowconfigure(0, weight=0)
        lists_frame.rowconfigure(1, weight=1)
        
        # Left column: Available Characters
        available_label = tk.Label(
            lists_frame,
            text="Available Characters",
            font=("Arial", 11, "bold")
        )
        available_label.grid(row=0, column=0, sticky="w", padx=5, pady=(0, 5))
        
        available_frame = tk.Frame(lists_frame, relief=tk.SUNKEN, borderwidth=1)
        available_frame.grid(row=1, column=0, sticky="nsew", padx=5)
        
        available_scroll = tk.Scrollbar(available_frame)
        available_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.available_listbox = tk.Listbox(
            available_frame,
            yscrollcommand=available_scroll.set,
            font=("Arial", 10)
        )
        self.available_listbox.pack(fill=tk.BOTH, expand=True)
        available_scroll.config(command=self.available_listbox.yview)
        
        # Bind click to add to selected
        self.available_listbox.bind("<Double-Button-1>", self._on_available_click)
        
        # Right column: Selected Participants
        selected_label = tk.Label(
            lists_frame,
            text="Selected Participants",
            font=("Arial", 11, "bold")
        )
        selected_label.grid(row=0, column=1, sticky="w", padx=5, pady=(0, 5))
        
        selected_frame = tk.Frame(lists_frame, relief=tk.SUNKEN, borderwidth=1)
        selected_frame.grid(row=1, column=1, sticky="nsew", padx=5)
        
        selected_scroll = tk.Scrollbar(selected_frame)
        selected_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.selected_listbox = tk.Listbox(
            selected_frame,
            yscrollcommand=selected_scroll.set,
            font=("Arial", 10)
        )
        self.selected_listbox.pack(fill=tk.BOTH, expand=True)
        selected_scroll.config(command=self.selected_listbox.yview)
        
        # Bind click to remove from selected
        self.selected_listbox.bind("<Double-Button-1>", self._on_selected_click)
        
        # Populate lists
        self._update_lists()
        
        # Add hint label
        hint_label = tk.Label(
            lists_frame,
            text="Double-click to add/remove characters",
            font=("Arial", 9),
            fg="gray"
        )
        hint_label.grid(row=2, column=0, columnspan=2, pady=(5, 0))
    
    def _create_buttons(self):
        """Create action buttons."""
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=10)
        
        start_button = tk.Button(
            button_frame,
            text="Start Event",
            command=self._on_start_clicked,
            width=15,
            font=("Arial", 10, "bold"),
            bg="#4CAF50",
            fg="white"
        )
        start_button.pack(side=tk.LEFT, padx=5)
        
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            command=self.window.destroy,
            width=15,
            font=("Arial", 10)
        )
        cancel_button.pack(side=tk.LEFT, padx=5)
    
    def _update_lists(self):
        """Update both listboxes with current state."""
        # Clear both lists
        self.available_listbox.delete(0, tk.END)
        self.selected_listbox.delete(0, tk.END)
        
        # Populate available (exclude already selected)
        selected_ids = {c.id for c in self.selected_participants}
        for char in self.available_characters:
            if char.id not in selected_ids:
                display_text = self._format_character(char)
                self.available_listbox.insert(tk.END, display_text)
        
        # Populate selected
        for char in self.selected_participants:
            display_text = self._format_character(char)
            self.selected_listbox.insert(tk.END, display_text)
    
    def _format_character(self, char: Any) -> str:
        """
        Format character for display in list.
        
        Args:
            char: Character object
            
        Returns:
            Formatted string with name and profession
        """
        name = char.callsign or char.name
        if char.profession:
            return f"{name} ({char.profession})"
        return name
    
    def _on_available_click(self, event):
        """Handle double-click on available character to add to selected."""
        selection = self.available_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        
        # Find the character (need to skip already selected ones)
        selected_ids = {c.id for c in self.selected_participants}
        available_chars = [c for c in self.available_characters if c.id not in selected_ids]
        
        if index < len(available_chars):
            char = available_chars[index]
            self.selected_participants.append(char)
            self._update_lists()
    
    def _on_selected_click(self, event):
        """Handle double-click on selected participant to remove."""
        selection = self.selected_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < len(self.selected_participants):
            self.selected_participants.pop(index)
            self._update_lists()
    
    def _on_start_clicked(self):
        """Handle Start Event button click."""
        # Call the callback with selected participants
        if self.on_start:
            self.on_start(self.selected_participants)
        
        # Close window
        self.window.destroy()
