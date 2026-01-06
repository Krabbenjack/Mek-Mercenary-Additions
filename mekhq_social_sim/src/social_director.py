"""
Social Director - Debug tool for observing event execution.

This window provides read-only visibility into:
- Event scheduling and execution
- Interaction selection
- Resolution results
- Emitted triggers
- Axis and pool deltas

The Social Director is strictly observer-only and does not:
- Influence outcomes
- Emit triggers
- Alter state
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Optional, List
from datetime import date
import json


class SocialDirectorWindow:
    """
    Debug window for observing event execution.
    
    Provides real-time visibility into event mechanics execution without
    influencing the outcome.
    """
    
    def __init__(self, parent: tk.Tk, event_manager=None):
        """
        Initialize Social Director window.
        
        Args:
            parent: Parent tkinter window
            event_manager: Optional EventManager instance to monitor
        """
        self.parent = parent
        self.event_manager = event_manager
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Social Director (Debug)")
        self.window.geometry("900x700")
        
        # Execution history
        self.execution_logs: List[dict] = []
        
        self._build_ui()
        
        # Register as observer if event manager is available
        if self.event_manager:
            self._register_observer()
    
    def _build_ui(self):
        """Build the Social Director UI."""
        # Top control bar
        control_frame = tk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(control_frame, text="Social Director - Event Execution Observer",
                font=("TkDefaultFont", 12, "bold")).pack(side=tk.LEFT)
        
        # Clear button
        ttk.Button(control_frame, text="Clear History", 
                  command=self._clear_history).pack(side=tk.RIGHT, padx=5)
        
        # Info label
        info_frame = tk.Frame(self.window, bg="#FFF9E6", relief=tk.FLAT, bd=1)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        info_text = ("ℹ️ Observer Mode: This window monitors event execution in real-time.\n"
                    "No actions here affect game state.")
        tk.Label(info_frame, text=info_text, bg="#FFF9E6", fg="#856404",
                font=("TkDefaultFont", 9), justify=tk.LEFT, anchor="w").pack(
                    fill=tk.X, padx=10, pady=8)
        
        # Main content area with two panes
        paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left pane: Execution log list
        left_frame = tk.Frame(paned)
        paned.add(left_frame, width=300)
        
        tk.Label(left_frame, text="Execution History", 
                font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Listbox for executions
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                      font=("TkDefaultFont", 9))
        self.log_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_listbox.yview)
        
        self.log_listbox.bind("<<ListboxSelect>>", self._on_log_select)
        
        # Right pane: Execution details
        right_frame = tk.Frame(paned)
        paned.add(right_frame, width=550)
        
        tk.Label(right_frame, text="Execution Details", 
                font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        # Scrolled text for details
        self.details_text = scrolledtext.ScrolledText(
            right_frame, 
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#F8F8F8",
            relief=tk.FLAT,
            bd=1
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        self.details_text.config(state=tk.DISABLED)
        
        # Status bar
        self.status_label = tk.Label(self.window, text="Waiting for events...", 
                                     anchor="w", relief=tk.SUNKEN, bd=1)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _register_observer(self):
        """Register as observer with the event injector."""
        try:
            from events.injector import get_event_injector
            injector = get_event_injector()
            injector.add_observer(self._on_event_executed)
            self._update_status("Connected to event injector")
        except Exception as e:
            self._update_status(f"Warning: Could not register observer: {e}")
    
    def _on_event_executed(self, log):
        """
        Callback for event execution.
        
        Args:
            log: EventExecutionLog object
        """
        # Convert to dict and store
        log_dict = log.to_dict()
        self.execution_logs.append(log_dict)
        
        # Update UI
        self._refresh_log_list()
        self._update_status(f"Event executed: {log_dict['event_name']}")
    
    def _refresh_log_list(self):
        """Refresh the execution log listbox."""
        self.log_listbox.delete(0, tk.END)
        
        for log in reversed(self.execution_logs):  # Most recent first
            event_name = log.get('event_name', 'Unknown')
            event_id = log.get('event_id', '?')
            exec_date = log.get('execution_date', '')
            
            # Format display
            display = f"[{exec_date}] {event_name} (ID:{event_id})"
            self.log_listbox.insert(tk.END, display)
    
    def _on_log_select(self, event):
        """Handle log selection in listbox."""
        selection = self.log_listbox.curselection()
        if not selection:
            return
        
        # Get selected log (reversed index)
        idx = len(self.execution_logs) - 1 - selection[0]
        log = self.execution_logs[idx]
        
        self._display_log_details(log)
    
    def _display_log_details(self, log: dict):
        """Display detailed information about an execution log."""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        # Format log details
        details = []
        details.append(f"═══ Event Execution Details ═══\n")
        details.append(f"Event: {log.get('event_name', 'Unknown')}")
        details.append(f"Event ID: {log.get('event_id', '?')}")
        details.append(f"Execution Date: {log.get('execution_date', '')}\n")
        
        # Participants
        participants = log.get('participants', [])
        details.append(f"─── Participants ({len(participants)}) ───")
        if participants:
            for p in participants:
                details.append(f"  • {p}")
        else:
            details.append("  (none)")
        details.append("")
        
        # Interactions
        interactions = log.get('interactions', [])
        details.append(f"─── Interactions ({len(interactions)}) ───")
        if interactions:
            for i, interaction in enumerate(interactions, 1):
                details.append(f"  {i}. {interaction}")
        else:
            details.append("  (none)")
        details.append("")
        
        # Resolution results
        results = log.get('resolution_results', [])
        details.append(f"─── Resolution Results ({len(results)}) ───")
        if results:
            for r in results:
                details.append(f"  • {r}")
        else:
            details.append("  (none)")
        details.append("")
        
        # Outcomes
        outcomes = log.get('outcomes', [])
        details.append(f"─── Outcomes ({len(outcomes)}) ───")
        if outcomes:
            for o in outcomes:
                details.append(f"  • {o}")
        else:
            details.append("  (none)")
        details.append("")
        
        # Triggers emitted
        triggers = log.get('triggers_emitted', [])
        details.append(f"─── Triggers Emitted ({len(triggers)}) ───")
        if triggers:
            for t in triggers:
                details.append(f"  • {t}")
        else:
            details.append("  (none)")
        details.append("")
        
        # Errors
        errors = log.get('errors', [])
        if errors:
            details.append(f"─── Errors ({len(errors)}) ───")
            for e in errors:
                details.append(f"  ⚠️ {e}")
            details.append("")
        
        # Write to text widget
        self.details_text.insert(1.0, "\n".join(details))
        self.details_text.config(state=tk.DISABLED)
    
    def _clear_history(self):
        """Clear execution history."""
        self.execution_logs.clear()
        self.log_listbox.delete(0, tk.END)
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.config(state=tk.DISABLED)
        self._update_status("History cleared")
    
    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_label.config(text=message)
