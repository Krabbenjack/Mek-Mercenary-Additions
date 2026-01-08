# Bookkeeping Application - Visual Reference

## Main Application Window

```
┌─────────────────────────────────────────────────────────────────┐
│ Bookkeeping Application                                    [_][□][×]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Journal Entry                                                  │
│                                                                 │
│           Date: [__________________________]                    │
│                  ↑ Light yellow when focused                    │
│                                                                 │
│      Reference: [__________________________]                    │
│                                                                 │
│  Debit Account: [__________________________] [Search]           │
│                  ↑ Click to open Account Search popup           │
│                                                                 │
│ Credit Account: [__________________________] [Search]           │
│                                                                 │
│         Amount: [__________________________]                    │
│                                                                 │
│    Description: [__________________________]                    │
│                                                                 │
│  [Save Entry]  [Clear]                                          │
│                                                                 │
│  Status: Ready                                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Focus Highlighting Behavior

### Before Focus (Default TEntry)
```
┌────────────────────────┐
│ Date:  [              ]│  ← White background (#FFFFFF)
│         border: 1px    │     Black text
└────────────────────────┘
```

### With Focus (Focus.TEntry)
```
┌────────────────────────┐
│ Date:  [▓▓▓▓▓▓▓▓▓▓▓▓▓▓]│  ← Light yellow background (#FFFFCC)
│         border: 2px    │     Black text, thicker border
└────────────────────────┘     Visual highlight for current field
```

## Account Search Popup (4-Column Layout)

```
┌──────────────────────────────────────────────────────────────────┐
│ Account Search                                         [_][□][×] │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Select an Account                                               │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │    1000     │  │    1100     │  │    1200     │  │   1210  ││
│  │Cash-Operatng│  │  Accounts   │  │ Inventory - │  │Inventory││
│  │   Account   │  │ Receivable  │  │Raw Materials│  │   WIP   ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │    1010     │  │    1200     │  │    1210     │  │   1220  ││
│  │Cash - Petty │  │ Inventory - │  │ Inventory - │  │Inventory││
│  │    Cash     │  │Raw Materials│  │     WIP     │  │Finished ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐│
│  │    1020     │  │    1300     │  │    1400     │  │   1410  ││
│  │Cash-Payroll │  │  Prepaid    │  │  Equipment  │  │Accum Dep││
│  │   Account   │  │  Expenses   │  │             │  │Equipment││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘│
│            ↑                                                     │
│     Currently highlighted with keyboard                         │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Keyboard Navigation in Account Search

### Arrow Key Movement

```
     Column 0      Column 1      Column 2      Column 3
     ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐
     │Acct0│ ────→ │Acct2│ ────→ │Acct4│ ────→ │Acct6│
     └─────┘       └─────┘       └─────┘       └─────┘
        ↓             ↓             ↓             ↓
     ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐
     │Acct1│ ────→ │Acct3│ ────→ │Acct5│ ────→ │Acct7│
     └─────┘       └─────┘       └─────┘       └─────┘
        ↓             ↓             ↓             ↓
     ┌─────┐       ┌─────┐       ┌─────┐       ┌─────┐
     │Acct8│ ────→ │Acct9│ ────→ │Acct10│────→ │Acct11│
     └─────┘       └─────┘       └─────┘       └─────┘

Legend:
  →  Right arrow key
  ↓  Down arrow key
  (Left/Up arrows work in reverse)
```

### Key Bindings

```
┌──────────────────────────────────────────────────────────┐
│ Key          │ Action                                    │
├──────────────┼───────────────────────────────────────────┤
│ ↑ (Up)       │ Move to account above in same column      │
│ ↓ (Down)     │ Move to account below in same column      │
│ ← (Left)     │ Move to account in column to the left     │
│ → (Right)    │ Move to account in column to the right    │
│ Enter        │ Select highlighted account → Insert → Close│
│ Escape       │ Cancel and close popup (no selection)     │
│ Mouse Click  │ Optional: Click any account to select     │
└──────────────┴───────────────────────────────────────────┘
```

## Top-to-Bottom, Left-to-Right Filling Algorithm

### Visual Representation

Given 12 accounts and 4 columns:

```
Input Order:  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

Display Layout (4 columns × 3 rows):

   Col 0    Col 1    Col 2    Col 3
   ─────    ─────    ─────    ─────
Row 0:  0       3       6       9
Row 1:  1       4       7      10
Row 2:  2       5       8      11

Algorithm: idx = column * num_rows + row
```

### Example with Real Accounts

```
  Column 0          Column 1          Column 2          Column 3
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ 1000          │ │ 1100          │ │ 1200          │ │ 1210          │
│ Cash-Operating│ │ Accounts Recv │ │ Inventory-Raw │ │ Inventory-WIP │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ 1010          │ │ 1200          │ │ 1210          │ │ 1220          │
│ Cash-PettyCash│ │ Inventory-Raw │ │ Inventory-WIP │ │ Inventory-Fin │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ 1020          │ │ 1300          │ │ 1400          │ │ 1410          │
│ Cash-Payroll  │ │ Prepaid Exp   │ │ Equipment     │ │ Accum Depr-Eq │
└───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
```

## Complete Workflow

```
1. User tabs to "Debit Account" field
   ┌──────────────────────┐
   │ Debit Account: [▓▓▓▓]│  ← Field highlighted (yellow)
   └──────────────────────┘

2. User clicks "Search" button or presses hotkey
   → Account Search popup opens, centered over main window

3. User navigates with arrow keys
   ┌─────────────────────────────┐
   │ Select an Account           │
   │ [Acct1] [Acct3] [▓Acct5▓]   │  ← Acct5 highlighted
   │ [Acct2] [Acct4] [Acct6]     │
   └─────────────────────────────┘

4. User presses Enter
   → "1200" is inserted into Debit Account field
   → Popup closes immediately

5. Result:
   ┌──────────────────────┐
   │ Debit Account: [1200]│  ← Account number inserted
   └──────────────────────┘
   Focus remains on the field or moves to next field
```

## TTK Style Configuration

### Code Structure

```python
# Initialize ttk.Style
style = ttk.Style()
style.theme_use("clam")  # TTK theme

# Default entry style
style.configure("TEntry",
    fieldbackground="white",    # ← TTK-compliant property
    foreground="black",
    borderwidth=1,
    relief="solid"
)

# Focus highlight style
style.configure("Focus.TEntry",
    fieldbackground="#FFFFCC",  # ← TTK-compliant property
    foreground="black",
    borderwidth=2,
    relief="solid"
)
```

### Event Binding Pattern

```python
# Create entry widget
entry = ttk.Entry(parent, width=40)

# Bind focus events
entry.bind("<FocusIn>", self.on_field_focus_in)
entry.bind("<FocusOut>", self.on_field_focus_out)

# Handler checks widget type before applying style
def on_field_focus_in(self, event):
    widget = event.widget
    if isinstance(widget, ttk.Entry):  # ← Type safety
        widget.configure(style="Focus.TEntry")

def on_field_focus_out(self, event):
    widget = event.widget
    if isinstance(widget, ttk.Entry):  # ← Type safety
        widget.configure(style="TEntry")
```

## Error Prevention

### What NOT to do (causes TclError)

```python
# ❌ WRONG - Will cause: TclError: unknown option "-bg"
entry = ttk.Entry(parent)
entry.configure(bg="yellow")        # ← Classic Tk property
entry.configure(background="yellow") # ← Classic Tk property
```

### What TO do (TTK-compliant)

```python
# ✅ CORRECT - TTK-compliant
style.configure("Focus.TEntry",
    fieldbackground="yellow"  # ← TTK property for entry background
)
entry = ttk.Entry(parent, style="Focus.TEntry")
```

## Summary

This implementation provides:
- ✓ **Production-safe** TTK styling (no TclError crashes)
- ✓ **Keyboard-first** navigation for speed
- ✓ **4-column layout** for maximum overview
- ✓ **Clean architecture** suitable for professional bookkeeping
- ✓ **Theme-safe** design that works with any TTK theme
- ✓ **Type-safe** focus handling (only affects ttk.Entry)
