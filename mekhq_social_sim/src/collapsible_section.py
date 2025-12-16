"""
Collapsible Section Widget for Tkinter

Provides a reusable collapsible/accordion section widget with header and body.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class CollapsibleSection(ttk.Frame):
    """
    A collapsible section widget with a header and expandable body.
    
    Features:
    - Click header to expand/collapse
    - Optional background color for header and body
    - Callback when section is opened/closed
    - Single-open mode support (externally managed)
    """
    
    def __init__(self, parent, title: str, bg_color: str = "#F0F0F0",
                 is_open: bool = False, on_toggle: Optional[Callable] = None):
        """
        Initialize the collapsible section.
        
        Args:
            parent: Parent widget
            title: Section title text
            bg_color: Background color for the section (pastel)
            is_open: Whether section starts open
            on_toggle: Callback function when section is toggled (receives section instance)
        """
        super().__init__(parent)
        
        self.title = title
        self.bg_color = bg_color
        self.is_open = is_open
        self.on_toggle = on_toggle
        
        # Create header frame
        self.header = tk.Frame(self, bg=bg_color, cursor="hand2")
        self.header.pack(fill=tk.X, padx=2, pady=(2, 0))
        
        # Header content
        header_content = tk.Frame(self.header, bg=bg_color)
        header_content.pack(fill=tk.X, expand=True, padx=10, pady=8)
        
        # Expand/collapse indicator
        self.indicator = tk.Label(
            header_content,
            text="▼" if is_open else "▶",
            bg=bg_color,
            fg="#1E1E1E",
            font=("TkDefaultFont", 10)
        )
        self.indicator.pack(side=tk.LEFT, padx=(0, 8))
        
        # Title label
        self.title_label = tk.Label(
            header_content,
            text=title,
            bg=bg_color,
            fg="#1E1E1E",
            font=("TkDefaultFont", 11, "bold")
        )
        self.title_label.pack(side=tk.LEFT)
        
        # Bind click events to header elements
        self.header.bind("<Button-1>", lambda e: self.toggle())
        self.indicator.bind("<Button-1>", lambda e: self.toggle())
        self.title_label.bind("<Button-1>", lambda e: self.toggle())
        
        # Body frame (scrollable container)
        self.body_container = tk.Frame(self, bg=bg_color)
        if is_open:
            self.body_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))
        
        # Content frame inside body (where user adds widgets)
        self.body = tk.Frame(self.body_container, bg=bg_color)
        self.body.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
    
    def toggle(self):
        """Toggle the section open/closed."""
        self.is_open = not self.is_open
        
        if self.is_open:
            self.indicator.config(text="▼")
            self.body_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))
        else:
            self.indicator.config(text="▶")
            self.body_container.pack_forget()
        
        # Call toggle callback if provided
        if self.on_toggle:
            self.on_toggle(self)
    
    def open(self):
        """Open the section (if not already open)."""
        if not self.is_open:
            self.toggle()
    
    def close(self):
        """Close the section (if not already closed)."""
        if self.is_open:
            self.toggle()
    
    def get_body(self) -> tk.Frame:
        """Get the body frame where content should be added."""
        return self.body


class AccordionContainer(ttk.Frame):
    """
    Container for multiple collapsible sections with single-open mode.
    
    When single_open=True, only one section can be open at a time.
    """
    
    def __init__(self, parent, single_open: bool = True):
        """
        Initialize the accordion container.
        
        Args:
            parent: Parent widget
            single_open: If True, only one section can be open at a time
        """
        super().__init__(parent)
        self.single_open = single_open
        self.sections = []
    
    def add_section(self, title: str, bg_color: str = "#F0F0F0",
                   is_open: bool = False) -> CollapsibleSection:
        """
        Add a new collapsible section to the accordion.
        
        Args:
            title: Section title
            bg_color: Background color for the section
            is_open: Whether section starts open
            
        Returns:
            The created CollapsibleSection
        """
        section = CollapsibleSection(
            self,
            title=title,
            bg_color=bg_color,
            is_open=is_open,
            on_toggle=self._on_section_toggle
        )
        section.pack(fill=tk.BOTH, expand=False, pady=(0, 4))
        self.sections.append(section)
        return section
    
    def _on_section_toggle(self, toggled_section: CollapsibleSection):
        """Handle section toggle event."""
        if self.single_open and toggled_section.is_open:
            # Close all other sections
            for section in self.sections:
                if section != toggled_section and section.is_open:
                    section.close()
