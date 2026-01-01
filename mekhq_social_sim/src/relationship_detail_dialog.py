"""
relationship_detail_dialog.py

Dialog for displaying detailed information about a single relationship.
This is a read-only view that displays runtime relationship data.

CRITICAL REQUIREMENTS:
- The UI MUST NOT compute any values
- The UI MUST NOT interpret rule JSONs
- The UI MUST NOT modify runtime state
- All data comes from the runtime provider via the adapter
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional
from models import Character


class RelationshipDetailDialog:
    """
    Popup window displaying detailed information about a single relationship.
    Shows axes, derived states, sentiments, flags, roles, and optional event history.
    """
    
    def __init__(self, parent: tk.Widget, relationship: Dict[str, Any],
                 char_a: Character, char_b: Character) -> None:
        """
        Initialize the relationship detail dialog.
        
        Args:
            parent: Parent widget
            relationship: Relationship data from runtime provider
            char_a: First character in the relationship
            char_b: Second character in the relationship
        """
        self.parent = parent
        self.relationship = relationship
        self.char_a = char_a
        self.char_b = char_b
        
        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Relationship: {char_a.name} ↔ {char_b.name}")
        self.window.geometry("700x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Main container with scrollbar
        canvas = tk.Canvas(self.window, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Build content sections
        self._build_header(scrollable_frame)
        self._build_axes_section(scrollable_frame)
        self._build_derived_section(scrollable_frame)
        self._build_sentiments_section(scrollable_frame)
        self._build_flags_section(scrollable_frame)
        self._build_roles_section(scrollable_frame)
        self._build_events_section(scrollable_frame)
        
        # Close button at bottom
        btn_frame = tk.Frame(scrollable_frame, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X, pady=20)
        
        close_btn = tk.Button(btn_frame, text="Close", command=self.window.destroy,
                              bg="#DDDDDD", padx=20, pady=5)
        close_btn.pack()
    
    def _build_header(self, parent: tk.Frame) -> None:
        """Build the header with character names."""
        header_frame = tk.Frame(parent, bg="#E8F5E9")
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Character A name
        label_a = tk.Label(header_frame, text=self.char_a.name,
                          bg="#E8F5E9", fg="#1E1E1E",
                          font=("TkDefaultFont", 14, "bold"))
        label_a.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Bidirectional arrow
        arrow = tk.Label(header_frame, text="↔", bg="#E8F5E9", fg="#1E1E1E",
                        font=("TkDefaultFont", 14))
        arrow.pack(side=tk.LEFT, padx=10)
        
        # Character B name
        label_b = tk.Label(header_frame, text=self.char_b.name,
                          bg="#E8F5E9", fg="#1E1E1E",
                          font=("TkDefaultFont", 14, "bold"))
        label_b.pack(side=tk.LEFT, padx=20, pady=10)
    
    def _build_axes_section(self, parent: tk.Frame) -> None:
        """Build the relationship axes section."""
        section_frame = tk.Frame(parent, bg="#FFFFFF")
        section_frame.pack(fill=tk.X, pady=10)
        
        title = tk.Label(section_frame, text="Relationship Axes",
                        bg="#FFFFFF", fg="#1E1E1E",
                        font=("TkDefaultFont", 12, "bold"))
        title.pack(anchor="w", pady=(0, 10))
        
        axes = self.relationship.get("axes", {})
        
        # Display each axis
        for axis_name in ["friendship", "romance", "respect"]:
            value = axes.get(axis_name, 0)
            self._build_axis_row(section_frame, axis_name.capitalize(), value)
    
    def _build_axis_row(self, parent: tk.Frame, label: str, value: int) -> None:
        """Build a single axis display row."""
        row = tk.Frame(parent, bg="#FFFFFF")
        row.pack(fill=tk.X, pady=5)
        
        # Label
        label_widget = tk.Label(row, text=f"{label}:", bg="#FFFFFF", fg="#1E1E1E",
                               font=("TkDefaultFont", 10), width=12, anchor="w")
        label_widget.pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar background
        bar_bg = tk.Frame(row, bg="#E0E0E0", height=20, width=300)
        bar_bg.pack(side=tk.LEFT, padx=(0, 10))
        bar_bg.pack_propagate(False)
        
        # Calculate bar width and color
        bar_width = int((abs(value) / 100.0) * 300)
        if value > 0:
            bar_color = self._get_positive_color(value)
            anchor = "w"
        elif value < 0:
            bar_color = self._get_negative_color(value)
            anchor = "e"
        else:
            bar_width = 0
            bar_color = "#E0E0E0"
            anchor = "w"
        
        # Progress bar fill
        if bar_width > 0:
            bar_fill = tk.Frame(bar_bg, bg=bar_color, height=20, width=bar_width)
            bar_fill.pack(side=tk.LEFT if value > 0 else tk.RIGHT, fill=tk.Y)
        
        # Value label
        value_str = f"+{value}" if value > 0 else str(value)
        value_label = tk.Label(row, text=value_str, bg="#FFFFFF",
                              fg=self._get_value_color(value),
                              font=("TkDefaultFont", 10, "bold"), width=5)
        value_label.pack(side=tk.LEFT)
    
    def _get_positive_color(self, value: int) -> str:
        """Get color for positive values."""
        if value >= 70:
            return "#2E7D32"  # Dark green
        elif value >= 40:
            return "#66BB6A"  # Light green
        else:
            return "#A5D6A7"  # Pale green
    
    def _get_negative_color(self, value: int) -> str:
        """Get color for negative values."""
        if value <= -70:
            return "#C62828"  # Dark red
        elif value <= -40:
            return "#EF5350"  # Light red
        else:
            return "#EF9A9A"  # Pale red
    
    def _get_value_color(self, value: int) -> str:
        """Get text color for value display."""
        if value > 20:
            return "#2E7D32"  # Dark green
        elif value < -20:
            return "#C62828"  # Dark red
        else:
            return "#757575"  # Gray
    
    def _build_derived_section(self, parent: tk.Frame) -> None:
        """Build the derived states and dynamics section."""
        derived = self.relationship.get("derived", {})
        
        if not derived:
            return
        
        section_frame = tk.Frame(parent, bg="#F5F5F5", relief=tk.RIDGE, borderwidth=1)
        section_frame.pack(fill=tk.X, pady=10)
        
        title = tk.Label(section_frame, text="Derived Information",
                        bg="#F5F5F5", fg="#1E1E1E",
                        font=("TkDefaultFont", 12, "bold"))
        title.pack(anchor="w", padx=10, pady=(10, 5))
        
        note = tk.Label(section_frame, text="(Read-only, derived from current relationship values)",
                       bg="#F5F5F5", fg="#757575",
                       font=("TkDefaultFont", 9, "italic"))
        note.pack(anchor="w", padx=10, pady=(0, 10))
        
        # States
        states = derived.get("states", {})
        if states:
            states_label = tk.Label(section_frame, text="Relationship States:",
                                   bg="#F5F5F5", fg="#1E1E1E",
                                   font=("TkDefaultFont", 10, "bold"))
            states_label.pack(anchor="w", padx=10, pady=(5, 2))
            
            for axis, state in states.items():
                state_row = tk.Label(section_frame,
                                    text=f"  • {axis.capitalize()}: {state}",
                                    bg="#F5F5F5", fg="#1E1E1E",
                                    font=("TkDefaultFont", 9))
                state_row.pack(anchor="w", padx=10, pady=1)
        
        # Dynamic
        dynamic = derived.get("dynamic", "")
        if dynamic and dynamic != "unknown":
            dynamic_label = tk.Label(section_frame, text="Relationship Dynamic:",
                                    bg="#F5F5F5", fg="#1E1E1E",
                                    font=("TkDefaultFont", 10, "bold"))
            dynamic_label.pack(anchor="w", padx=10, pady=(10, 2))
            
            dynamic_value = tk.Label(section_frame,
                                    text=f"  • {dynamic.capitalize()}",
                                    bg="#F5F5F5", fg="#1E1E1E",
                                    font=("TkDefaultFont", 9))
            dynamic_value.pack(anchor="w", padx=10, pady=(0, 10))
    
    def _build_sentiments_section(self, parent: tk.Frame) -> None:
        """Build the sentiments section."""
        sentiments = self.relationship.get("sentiments", {})
        
        if not sentiments:
            return
        
        section_frame = tk.Frame(parent, bg="#FFF9E6")
        section_frame.pack(fill=tk.X, pady=10)
        
        title = tk.Label(section_frame, text="Sentiments",
                        bg="#FFF9E6", fg="#1E1E1E",
                        font=("TkDefaultFont", 12, "bold"))
        title.pack(anchor="w", padx=10, pady=10)
        
        for sentiment_name, sentiment_data in sentiments.items():
            self._build_sentiment_row(section_frame, sentiment_name, sentiment_data)
    
    def _build_sentiment_row(self, parent: tk.Frame, name: str, data: Any) -> None:
        """Build a single sentiment display row."""
        row = tk.Frame(parent, bg="#FFF9E6")
        row.pack(fill=tk.X, padx=10, pady=2)
        
        # Sentiment name
        name_label = tk.Label(row, text=f"• {name}",
                             bg="#FFF9E6", fg="#1E1E1E",
                             font=("TkDefaultFont", 10, "bold"))
        name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Strength if available
        if isinstance(data, dict) and "strength" in data:
            strength = data["strength"]
            strength_label = tk.Label(row, text=f"Strength: {strength}",
                                     bg="#FFF9E6", fg="#757575",
                                     font=("TkDefaultFont", 9))
            strength_label.pack(side=tk.LEFT)
    
    def _build_flags_section(self, parent: tk.Frame) -> None:
        """Build the flags section."""
        flags = self.relationship.get("flags", {})
        
        if not flags:
            return
        
        section_frame = tk.Frame(parent, bg="#FFE6E6")
        section_frame.pack(fill=tk.X, pady=10)
        
        title = tk.Label(section_frame, text="Flags (Temporary States)",
                        bg="#FFE6E6", fg="#1E1E1E",
                        font=("TkDefaultFont", 12, "bold"))
        title.pack(anchor="w", padx=10, pady=10)
        
        for flag_name, flag_data in flags.items():
            self._build_flag_row(section_frame, flag_name, flag_data)
    
    def _build_flag_row(self, parent: tk.Frame, name: str, data: Any) -> None:
        """Build a single flag display row."""
        row = tk.Frame(parent, bg="#FFE6E6")
        row.pack(fill=tk.X, padx=10, pady=2)
        
        # Flag name
        name_label = tk.Label(row, text=f"⚑ {name}",
                             bg="#FFE6E6", fg="#1E1E1E",
                             font=("TkDefaultFont", 10, "bold"))
        name_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Duration if available
        if isinstance(data, dict) and "remaining_days" in data:
            days = data["remaining_days"]
            duration_label = tk.Label(row, text=f"{days} days remaining",
                                     bg="#FFE6E6", fg="#D32F2F",
                                     font=("TkDefaultFont", 9))
            duration_label.pack(side=tk.LEFT)
    
    def _build_roles_section(self, parent: tk.Frame) -> None:
        """Build the roles section."""
        roles = self.relationship.get("roles", {})
        
        if not roles:
            return
        
        section_frame = tk.Frame(parent, bg="#E8EAF6")
        section_frame.pack(fill=tk.X, pady=10)
        
        title = tk.Label(section_frame, text="Relationship Roles",
                        bg="#E8EAF6", fg="#1E1E1E",
                        font=("TkDefaultFont", 12, "bold"))
        title.pack(anchor="w", padx=10, pady=10)
        
        # Get participants
        participants = self.relationship.get("participants", {})
        char_a_id = participants.get("a", "")
        char_b_id = participants.get("b", "")
        
        for role_name, role_holder in roles.items():
            # Determine which character has this role
            if role_holder == char_a_id:
                role_text = f"{role_name}: {self.char_a.name}"
            elif role_holder == char_b_id:
                role_text = f"{role_name}: {self.char_b.name}"
            else:
                role_text = f"{role_name}: Unknown"
            
            role_label = tk.Label(section_frame, text=f"• {role_text}",
                                 bg="#E8EAF6", fg="#1E1E1E",
                                 font=("TkDefaultFont", 10))
            role_label.pack(anchor="w", padx=10, pady=2)
    
    def _build_events_section(self, parent: tk.Frame) -> None:
        """Build the optional recent events section (collapsible)."""
        events = self.relationship.get("events", [])
        
        if not events:
            return
        
        # Create collapsible section
        section_frame = tk.Frame(parent, bg="#F0F0F0")
        section_frame.pack(fill=tk.X, pady=10)
        
        # Header with toggle button
        header = tk.Frame(section_frame, bg="#F0F0F0")
        header.pack(fill=tk.X)
        
        self.events_visible = tk.BooleanVar(value=False)
        
        toggle_btn = tk.Button(header, text="▶ Recent Events",
                              command=self._toggle_events,
                              bg="#F0F0F0", relief=tk.FLAT,
                              font=("TkDefaultFont", 10, "bold"),
                              anchor="w")
        toggle_btn.pack(fill=tk.X, padx=10, pady=5)
        
        self.toggle_btn = toggle_btn
        
        # Events content (initially hidden)
        self.events_content = tk.Frame(section_frame, bg="#F0F0F0")
        
        for event in events[:10]:  # Show max 10 recent events
            self._build_event_row(self.events_content, event)
    
    def _toggle_events(self) -> None:
        """Toggle the visibility of the events section."""
        if self.events_visible.get():
            self.events_content.pack_forget()
            self.toggle_btn.config(text="▶ Recent Events")
            self.events_visible.set(False)
        else:
            self.events_content.pack(fill=tk.X, padx=10, pady=(0, 10))
            self.toggle_btn.config(text="▼ Recent Events")
            self.events_visible.set(True)
    
    def _build_event_row(self, parent: tk.Frame, event: Dict[str, Any]) -> None:
        """Build a single event display row."""
        row = tk.Frame(parent, bg="#F0F0F0")
        row.pack(fill=tk.X, pady=2)
        
        event_name = event.get("name", "Unknown event")
        days_ago = event.get("days_ago", 0)
        
        event_label = tk.Label(row, text=f"• {event_name} — {days_ago} days ago",
                              bg="#F0F0F0", fg="#1E1E1E",
                              font=("TkDefaultFont", 9))
        event_label.pack(anchor="w", padx=5, pady=1)
