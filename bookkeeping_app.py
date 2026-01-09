#!/usr/bin/env python3
"""
Bookkeeping Application - Keyboard-First TTK-Based UI

A production-ready bookkeeping application with:
1. TTK-compliant focus highlighting using ttk.Style
2. 4-column account search popup with keyboard navigation
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Optional


# Sample account data for demonstration
ACCOUNTS = [
    ("1000", "Cash - Operating Account"),
    ("1010", "Cash - Petty Cash"),
    ("1020", "Cash - Payroll Account"),
    ("1100", "Accounts Receivable"),
    ("1200", "Inventory - Raw Materials"),
    ("1210", "Inventory - Work in Progress"),
    ("1220", "Inventory - Finished Goods"),
    ("1300", "Prepaid Expenses"),
    ("1400", "Equipment"),
    ("1410", "Accumulated Depreciation - Equipment"),
    ("1500", "Vehicles"),
    ("1510", "Accumulated Depreciation - Vehicles"),
    ("2000", "Accounts Payable"),
    ("2100", "Salaries Payable"),
    ("2200", "Interest Payable"),
    ("2300", "Taxes Payable"),
    ("2400", "Notes Payable - Short Term"),
    ("2500", "Notes Payable - Long Term"),
    ("3000", "Owner's Equity"),
    ("3100", "Retained Earnings"),
    ("4000", "Sales Revenue"),
    ("4100", "Service Revenue"),
    ("4200", "Interest Income"),
    ("5000", "Cost of Goods Sold"),
    ("6000", "Salaries Expense"),
    ("6100", "Rent Expense"),
    ("6200", "Utilities Expense"),
    ("6300", "Insurance Expense"),
    ("6400", "Depreciation Expense"),
    ("6500", "Office Supplies Expense"),
    ("6600", "Marketing Expense"),
    ("6700", "Travel Expense"),
]


class AccountSearchPopup(tk.Toplevel):
    """
    Account Search Popup with 4-column layout and keyboard navigation.
    
    Features:
    - Displays accounts in exactly 4 columns
    - Top-to-bottom, left-to-right filling
    - Arrow key navigation across rows and columns
    - Enter to select, Esc to cancel
    - Centers over parent window
    """
    
    def __init__(self, parent: tk.Widget, target_entry: ttk.Entry, accounts: List[Tuple[str, str]]):
        super().__init__(parent)
        
        self.target_entry = target_entry
        self.accounts = accounts
        self.selected_account = None
        self.current_row = 0
        self.current_col = 0
        
        # Window configuration
        self.title("Account Search")
        self.transient(parent)
        self.grab_set()
        
        # Calculate layout
        self.num_columns = 4
        self.num_rows = (len(accounts) + self.num_columns - 1) // self.num_columns
        
        # Create UI
        self._create_widgets()
        self._center_on_parent(parent)
        
        # Keyboard bindings
        self.bind("<Escape>", lambda e: self._cancel())
        self.bind("<Return>", lambda e: self._select_current())
        self.bind("<Up>", lambda e: self._navigate(-1, 0))
        self.bind("<Down>", lambda e: self._navigate(1, 0))
        self.bind("<Left>", lambda e: self._navigate(0, -1))
        self.bind("<Right>", lambda e: self._navigate(0, 1))
        
        # Focus first button
        if self.buttons:
            self.buttons[0][0].focus_set()
    
    def _create_widgets(self):
        """Create 4-column layout with account buttons."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Title label
        title_label = ttk.Label(
            main_frame,
            text="Select an Account",
            font=("TkDefaultFont", 12, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 10), sticky="w")
        
        # Create 4-column grid of account buttons
        self.buttons: List[List[ttk.Button]] = []
        
        for row in range(self.num_rows):
            button_row = []
            for col in range(self.num_columns):
                idx = col * self.num_rows + row  # Top-to-bottom, left-to-right
                
                if idx < len(self.accounts):
                    account_num, account_name = self.accounts[idx]
                    
                    # Create frame for each account entry
                    account_frame = ttk.Frame(main_frame)
                    account_frame.grid(row=row + 1, column=col, padx=5, pady=2, sticky="ew")
                    
                    # Account button with number and name
                    btn_text = f"{account_num}\n{account_name}"
                    btn = ttk.Button(
                        account_frame,
                        text=btn_text,
                        command=lambda acc=account_num: self._select_account(acc)
                    )
                    btn.pack(fill="both", expand=True)
                    
                    # Store button reference
                    button_row.append(btn)
                    
                    # Mouse click binding
                    btn.bind("<Button-1>", lambda e, acc=account_num: self._select_account(acc))
                else:
                    # Empty cell
                    button_row.append(None)
            
            self.buttons.append(button_row)
        
        # Configure column weights for even distribution
        for col in range(self.num_columns):
            main_frame.columnconfigure(col, weight=1, uniform="cols")
    
    def _center_on_parent(self, parent: tk.Widget):
        """Center popup over parent window."""
        self.update_idletasks()
        
        # Get parent window position and size
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        
        # Get popup size
        popup_w = self.winfo_reqwidth()
        popup_h = self.winfo_reqheight()
        
        # Calculate center position
        x = parent_x + (parent_w - popup_w) // 2
        y = parent_y + (parent_h - popup_h) // 2
        
        # Ensure popup is on screen
        x = max(0, x)
        y = max(0, y)
        
        self.geometry(f"+{x}+{y}")
    
    def _navigate(self, row_delta: int, col_delta: int):
        """Navigate between account buttons using arrow keys."""
        new_row = self.current_row + row_delta
        new_col = self.current_col + col_delta
        
        # Boundary checks
        if 0 <= new_row < len(self.buttons) and 0 <= new_col < len(self.buttons[0]):
            # Check if target button exists
            if self.buttons[new_row][new_col] is not None:
                self.current_row = new_row
                self.current_col = new_col
                self.buttons[new_row][new_col].focus_set()
    
    def _select_current(self):
        """Select the currently focused account."""
        if self.buttons and self.buttons[self.current_row][self.current_col]:
            # Extract account number from button text
            btn = self.buttons[self.current_row][self.current_col]
            account_text = btn.cget("text")
            account_num = account_text.split("\n")[0]
            self._select_account(account_num)
    
    def _select_account(self, account_num: str):
        """Select an account and close the popup."""
        self.selected_account = account_num
        
        # Insert into target entry
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, account_num)
        
        # Close popup
        self.destroy()
    
    def _cancel(self):
        """Cancel selection and close popup."""
        self.selected_account = None
        self.destroy()


class BookkeepingApp:
    """
    Main bookkeeping application with keyboard-first design.
    
    Features:
    - TTK-compliant focus highlighting using fieldbackground
    - Account search popup with 4-column layout
    - Keyboard navigation throughout
    """
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bookkeeping Application")
        self.root.geometry("800x600")
        
        # Initialize ttk.Style for focus highlighting
        self.style = ttk.Style()
        self._setup_styles()
        
        # Create UI
        self._create_widgets()
    
    def _setup_styles(self):
        """
        Set up TTK styles including dedicated focus style.
        
        Focus.TEntry uses fieldbackground for highlighting (ttk-compliant).
        """
        # Use a theme that supports fieldbackground
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass  # Use default theme if clam not available
        
        # Configure default TEntry style
        self.style.configure(
            "TEntry",
            fieldbackground="white",
            foreground="black",
            borderwidth=1,
            relief="solid"
        )
        
        # Configure Focus.TEntry style with highlighted fieldbackground
        self.style.configure(
            "Focus.TEntry",
            fieldbackground="#FFFFCC",  # Light yellow highlight
            foreground="black",
            borderwidth=2,
            relief="solid"
        )
    
    def _create_widgets(self):
        """Create main application widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Journal Entry",
            font=("TkDefaultFont", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20), sticky="w")
        
        # Entry form fields
        fields = [
            ("Date:", "date_entry"),
            ("Reference:", "ref_entry"),
            ("Debit Account:", "debit_account_entry"),
            ("Credit Account:", "credit_account_entry"),
            ("Amount:", "amount_entry"),
            ("Description:", "desc_entry"),
        ]
        
        self.entries = {}
        
        for idx, (label_text, entry_name) in enumerate(fields):
            row = idx + 1
            
            # Label
            label = ttk.Label(main_frame, text=label_text, width=15, anchor="e")
            label.grid(row=row, column=0, padx=(0, 10), pady=5, sticky="e")
            
            # Entry field
            entry = ttk.Entry(main_frame, width=40)
            entry.grid(row=row, column=1, pady=5, sticky="ew")
            
            # Bind focus events for ttk.Entry widgets
            entry.bind("<FocusIn>", self.on_field_focus_in)
            entry.bind("<FocusOut>", self.on_field_focus_out)
            
            self.entries[entry_name] = entry
            
            # Add search button for account fields
            if "account" in entry_name:
                search_btn = ttk.Button(
                    main_frame,
                    text="Search",
                    command=lambda e=entry: self._open_account_search(e)
                )
                search_btn.grid(row=row, column=2, padx=(5, 0), pady=5)
        
        # Configure column weights
        main_frame.columnconfigure(1, weight=1)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=len(fields) + 1, column=0, columnspan=3, pady=(20, 0), sticky="ew")
        
        save_btn = ttk.Button(button_frame, text="Save Entry", command=self._save_entry)
        save_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = ttk.Button(button_frame, text="Clear", command=self._clear_form)
        clear_btn.pack(side="left")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief="sunken",
            anchor="w"
        )
        status_label.grid(row=len(fields) + 2, column=0, columnspan=3, pady=(20, 0), sticky="ew")
    
    def on_field_focus_in(self, event):
        """
        Handle FocusIn event for ttk.Entry widgets.
        
        Applies Focus.TEntry style to highlight the focused field.
        Only affects ttk.Entry widgets.
        """
        widget = event.widget
        
        # Verify this is a ttk.Entry widget
        if isinstance(widget, ttk.Entry):
            widget.configure(style="Focus.TEntry")
    
    def on_field_focus_out(self, event):
        """
        Handle FocusOut event for ttk.Entry widgets.
        
        Restores default TEntry style when field loses focus.
        Only affects ttk.Entry widgets.
        """
        widget = event.widget
        
        # Verify this is a ttk.Entry widget
        if isinstance(widget, ttk.Entry):
            widget.configure(style="TEntry")
    
    def _open_account_search(self, target_entry: ttk.Entry):
        """Open account search popup for the given entry field."""
        AccountSearchPopup(self.root, target_entry, ACCOUNTS)
    
    def _save_entry(self):
        """Save journal entry (placeholder)."""
        # Validate fields
        date_val = self.entries["date_entry"].get()
        debit_acc = self.entries["debit_account_entry"].get()
        credit_acc = self.entries["credit_account_entry"].get()
        amount = self.entries["amount_entry"].get()
        
        if not all([date_val, debit_acc, credit_acc, amount]):
            self.status_var.set("Error: All fields are required")
            return
        
        # Placeholder save action
        self.status_var.set(f"Entry saved: Debit {debit_acc}, Credit {credit_acc}, Amount {amount}")
    
    def _clear_form(self):
        """Clear all form fields."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.status_var.set("Form cleared")


def main():
    """Main entry point."""
    root = tk.Tk()
    app = BookkeepingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
