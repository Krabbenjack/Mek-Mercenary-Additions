# Bookkeeping Application - TTK-Compliant Implementation

A professional, keyboard-first bookkeeping application built with Python Tkinter and TTK widgets.

## Features

### Task 1: TTK-Compliant Focus Highlighting ✓

The application implements proper TTK-style focus highlighting that avoids the common `_tkinter.TclError: unknown option "-bg"` error.

**Implementation Details:**

- **Dedicated Focus Style**: Uses `Focus.TEntry` style defined via `ttk.Style`
- **TTK-Compliant**: Uses `fieldbackground` property instead of `bg` or `background`
- **Type-Safe**: Focus handlers verify widget type with `isinstance(widget, ttk.Entry)`
- **Clean Event Handling**:
  - `on_field_focus_in()`: Applies `Focus.TEntry` style with light yellow highlight
  - `on_field_focus_out()`: Restores default `TEntry` style
- **Theme-Safe**: Works with any TTK theme
- **Non-Intrusive**: Only affects `ttk.Entry` widgets, leaves other widgets unchanged

**Visual Effect:**
- Unfocused entry: White background (`#FFFFFF`)
- Focused entry: Light yellow background (`#FFFFCC`)
- Border width increases from 1 to 2 pixels on focus

### Task 2: Account Search Popup with 4-Column Layout ✓

A specialized popup window for quickly finding and selecting account numbers.

**Layout Specifications:**

- **Exactly 4 columns** of account entries
- **Top-to-bottom, left-to-right filling** algorithm
- Each entry displays:
  - Account number (e.g., `1000`)
  - Account name/description (e.g., `Cash - Operating Account`)

**Keyboard Navigation:**

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate up/down within current column |
| `←` `→` | Navigate left/right between columns |
| `Enter` | Select highlighted account |
| `Escape` | Cancel and close popup |

**Additional Features:**

- **Auto-centering**: Popup opens centered over parent window
- **Smart sizing**: Adjusts to content without excessive height
- **Immediate action**: Selected account number is instantly inserted into originating field
- **Auto-close**: Popup closes immediately after selection
- **Mouse support**: Click any account button to select (but not required)

### Sample Account Data

Includes 32 pre-configured accounts covering:
- Assets (1000-1510): Cash, receivables, inventory, equipment, vehicles
- Liabilities (2000-2500): Payables, salaries, taxes, notes
- Equity (3000-3100): Owner's equity, retained earnings
- Revenue (4000-4200): Sales, services, interest income
- Expenses (5000-6700): COGS, salaries, rent, utilities, and more

## Usage

### Running the Application

```bash
python3 bookkeeping_app.py
```

### Basic Workflow

1. **Enter Journal Entry Data**:
   - Date, Reference, Debit Account, Credit Account, Amount, Description
   
2. **Finding Accounts**:
   - Click "Search" button next to account field, or
   - Tab to the account field and click the search button
   
3. **In Account Search Popup**:
   - Use arrow keys to navigate
   - Press Enter to select
   - Or click with mouse
   
4. **Complete Entry**:
   - Fill remaining fields
   - Click "Save Entry" or press associated hotkey

### Focus Highlighting in Action

When tabbing through fields:
1. Current field gets light yellow background
2. Border becomes more prominent
3. Previous field returns to normal appearance
4. Visual feedback is immediate and clear

## Technical Architecture

### TTK Style System

```python
# Default style
style.configure("TEntry",
    fieldbackground="white",
    foreground="black",
    borderwidth=1
)

# Focus highlight style
style.configure("Focus.TEntry",
    fieldbackground="#FFFFCC",  # Light yellow
    foreground="black",
    borderwidth=2
)
```

### Focus Event Handlers

```python
def on_field_focus_in(self, event):
    """Apply focus highlight to ttk.Entry widgets only."""
    widget = event.widget
    if isinstance(widget, ttk.Entry):
        widget.configure(style="Focus.TEntry")

def on_field_focus_out(self, event):
    """Restore default style to ttk.Entry widgets only."""
    widget = event.widget
    if isinstance(widget, ttk.Entry):
        widget.configure(style="TEntry")
```

### Account Search Algorithm

**Top-to-Bottom, Left-to-Right Filling:**

```python
for row in range(num_rows):
    for col in range(num_columns):
        idx = col * num_rows + row  # Key algorithm
        if idx < len(accounts):
            # Create button for accounts[idx]
```

**Example with 8 accounts, 4 columns:**

```
Column 0  Column 1  Column 2  Column 3
--------  --------  --------  --------
Acct 0    Acct 2    Acct 4    Acct 6
Acct 1    Acct 3    Acct 5    Acct 7
```

## Testing

Run the comprehensive test suite:

```bash
python3 test_bookkeeping_app.py
```

**Test Coverage:**
- ✓ TTK-compliant focus highlighting (6 tests)
- ✓ Account search popup functionality (8 tests)
- ✓ Keyboard-first design (2 tests)
- ✓ Code quality (3 tests)
- ✓ TTK compliance (3 tests)

**All 22 tests pass** ✓

## Requirements Met

### Task 1 Requirements ✓

- [x] No use of `bg`, `background`, or classic Tk styling on ttk widgets
- [x] Use `ttk.Style` to define dedicated focus style (`Focus.TEntry`)
- [x] Focused `ttk.Entry` visually highlighted using `fieldbackground`
- [x] `<FocusIn>` applies focus style only if widget is `ttk.Entry`
- [x] `<FocusOut>` restores default `TEntry` style
- [x] Non-Entry widgets are not affected
- [x] Solution is theme-safe
- [x] Keyboard navigation is not broken

### Task 2 Requirements ✓

- [x] Display accounts in exactly four columns
- [x] Each column entry shows account number and name/description
- [x] Accounts filled top-to-bottom, then left-to-right
- [x] Popup opens centered over parent window
- [x] Popup resizes sensibly without excessive height
- [x] Arrow keys move logically across rows and columns
- [x] Enter selects the highlighted account
- [x] Escape closes the popup without selection
- [x] Mouse interaction exists but is not required
- [x] Selected account number inserted into originating field
- [x] Popup closes immediately after selection
- [x] Fully TTK-compatible implementation

## Code Quality

- **Clean, maintainable code** with descriptive variable names
- **Comprehensive docstrings** for classes and methods
- **Type hints** for better IDE support and clarity
- **No external dependencies** beyond Python standard library
- **Professional structure** suitable for production use
- **Keyboard-first design** optimized for bookkeeping workflows

## Future Enhancements

Potential improvements for production deployment:
- Database backend for account storage
- Transaction history and reporting
- Account balance calculations
- Multi-user support
- Export to CSV/Excel
- Advanced search/filtering
- Configurable themes
- Accessibility features (screen reader support)

## License

This implementation is provided as a reference for TTK-compliant focus handling and keyboard-first UI design patterns.
