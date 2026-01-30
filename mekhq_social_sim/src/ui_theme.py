"""
ui_theme.py

Zentrales Dark / Military Theme für die Main UI.
- keine Assets
- vollständig codebasiert
- klare Style-Namen
- gedacht für ttk-basierte Main UI

WICHTIG:
Dieses Theme ist für die HAUPT-UI gedacht.
Detail-Dialoge (Character Detail Window) dürfen bewusst abweichen.
"""

import tkinter.ttk as ttk


# ------------------------------------------------------------
# Zentrale Farbdefinition (EINZIGE Quelle für Farben)
# ------------------------------------------------------------

THEME = {
    # Base backgrounds
    "bg_main": "#1E1F22",        # sehr dunkles Anthrazit
    "bg_panel": "#25272B",       # Panel-Hintergrund
    "bg_raised": "#2E3136",      # leicht angehobene Blöcke
    "bg_highlight": "#3A3F45",   # Hover / Selection

    # Foregrounds
    "fg_primary": "#E6E6E6",     # Haupttext
    "fg_secondary": "#A9ADB4",   # Sekundärtext
    "fg_muted": "#7A7F87",       # Meta / Labels

    # Akzentfarben (sparsam!)
    "accent_command": "#4E7A3D", # gedämpftes Olivgrün
    "accent_alert": "#9E4A3A",   # gedecktes Rot
    "accent_info": "#4A6E8A",    # Stahlblau
    "accent_debug": "#6B5A8E"    # Debug-Violett
}

# ------------------------------------------------------------
# Dark Grey Theme for Event Resolve Window (exact hex values)
# ------------------------------------------------------------

RESOLVE_THEME = {
    # Backgrounds
    "window_bg": "#1E1F22",       # Window background
    "header_bg": "#26282C",       # Header background
    "panel_bg": "#232428",        # Panel background
    "card_bg": "#2A2C31",         # Card background
    "card_hover": "#32343A",      # Card hover
    "border": "#3A3D44",          # Border/separator
    
    # Text
    "text_primary": "#E6E6E6",    # Primary text
    "text_secondary": "#B7BCC5",  # Secondary text
    "text_muted": "#8D93A1",      # Muted text
    
    # Accent
    "accent": "#6C8CF5",          # Accent (buttons/chips outline)
    "accent_hover": "#7A98FF",    # Accent hover
    "success": "#4CAF50",         # Success badge
    "fail": "#E05D5D",            # Fail badge
    "warning": "#F0C15C",         # Warning/info
    
    # Button backgrounds
    "btn_primary_bg": "#6C8CF5",
    "btn_primary_hover": "#7A98FF",
    "btn_primary_text": "#0E1014",
    "btn_secondary_bg": "#2A2C31",
    "btn_secondary_hover": "#32343A",
    "btn_secondary_border": "#3A3D44",
    "btn_secondary_text": "#E6E6E6",
}


# ------------------------------------------------------------
# Style Initialisierung
# ------------------------------------------------------------

def init_dark_military_style(root):
    """
    Initialisiert das Dark / Military ttk-Theme.
    Diese Funktion MUSS genau einmal nach tk.Tk() aufgerufen werden.
    """

    style = ttk.Style(root)

    # Native Themes vermeiden (clam ist am berechenbarsten)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # --------------------------------------------------------
    # Frames
    # --------------------------------------------------------

    style.configure(
        "Main.TFrame",
        background=THEME["bg_main"]
    )

    style.configure(
        "Panel.TFrame",
        background=THEME["bg_panel"]
    )

    style.configure(
        "Raised.TFrame",
        background=THEME["bg_raised"]
    )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    style.configure(
        "Primary.TLabel",
        background=THEME["bg_panel"],
        foreground=THEME["fg_primary"]
    )

    style.configure(
        "Secondary.TLabel",
        background=THEME["bg_panel"],
        foreground=THEME["fg_secondary"]
    )

    style.configure(
        "Muted.TLabel",
        background=THEME["bg_panel"],
        foreground=THEME["fg_muted"]
    )

    style.configure(
        "Context.TLabel",
        background=THEME["bg_panel"],
        foreground=THEME["fg_muted"],
        font=("TkDefaultFont", 9, "bold")
    )

    # --------------------------------------------------------
    # Buttons
    # --------------------------------------------------------

    style.configure(
        "Primary.TButton",
        background=THEME["bg_highlight"],
        foreground=THEME["fg_primary"],
        padding=(8, 4),
        relief="flat"
    )

    style.map(
        "Primary.TButton",
        background=[
            ("active", THEME["bg_raised"]),
            ("pressed", THEME["bg_highlight"])
        ]
    )

    style.configure(
        "Debug.TButton",
        background=THEME["bg_panel"],
        foreground=THEME["accent_debug"],
        padding=(6, 3),
        relief="flat"
    )

    style.map(
        "Debug.TButton",
        foreground=[
            ("active", THEME["fg_primary"])
        ]
    )

    # --------------------------------------------------------
    # Treeview
    # --------------------------------------------------------

    style.configure(
        "Treeview",
        background=THEME["bg_panel"],
        fieldbackground=THEME["bg_panel"],
        foreground=THEME["fg_primary"],
        borderwidth=0,
        relief="flat"
    )

    style.map(
        "Treeview",
        background=[
            ("selected", THEME["bg_highlight"])
        ],
        foreground=[
            ("selected", THEME["fg_primary"])
        ]
    )

    style.configure(
        "Treeview.Heading",
        background=THEME["bg_panel"],
        foreground=THEME["fg_secondary"],
        relief="flat"
    )

    # --------------------------------------------------------
    # Notebook (solange es existiert)
    # --------------------------------------------------------

    style.configure(
        "TNotebook",
        background=THEME["bg_main"],
        borderwidth=0
    )

    style.configure(
        "TNotebook.Tab",
        background=THEME["bg_panel"],
        foreground=THEME["fg_secondary"],
        padding=(10, 4)
    )

    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", THEME["bg_raised"])
        ],
        foreground=[
            ("selected", THEME["fg_primary"])
        ]
    )

    return style
