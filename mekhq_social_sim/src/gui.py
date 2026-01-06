from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, Optional, List
from datetime import date, timedelta, datetime
import json
import traceback

# Ensure src is on sys.path so the merk_calendar package is importable.
repo_root = Path(__file__).resolve().parents[2]  # mekhq_social_sim/src/gui.py -> repo root
src_path = repo_root.joinpath("src")
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Define canonical export directory
EXPORT_DIR = repo_root / "mekhq_social_sim" / "exports"

# Calendar system imports (required by the full integration)
try:
    from events import EventManager, RecurrenceType
    from merk_calendar.calendar_system import DetailedCalendarWindow, DatePickerDialog
    EVENTS_PACKAGE_AVAILABLE = True
except Exception:
    try:
        from merk_calendar.calendar_system import (
            EventManager,
            RecurrenceType,
            DetailedCalendarWindow,
            DatePickerDialog,
        )
        EVENTS_PACKAGE_AVAILABLE = False
    except Exception:
        # If calendar package is missing the GUI still runs, calendar features are disabled.
        EventManager = None
        RecurrenceType = None
        DetailedCalendarWindow = None
        DatePickerDialog = None
        EVENTS_PACKAGE_AVAILABLE = False

from models import Character
from data_loading import load_campaign, apply_toe_structure, load_campaign_metadata
from interaction_pool import reset_daily_pools
from trait_synergy_engine import get_character_traits_as_enums
from rank_resolver import get_rank_resolver
from collapsible_section import AccordionContainer
from skill_attribute_mapping import format_skill_support
import mekhq_personnel_exporter
from relationship_ui_adapter import RelationshipRuntimeAdapter
from relationship_detail_dialog import RelationshipDetailDialog
from ui_theme import init_dark_military_style, THEME

# Try to import PIL for image handling
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# Shared portrait base path used by all portrait handling code
PORTRAIT_BASE_PATH = Path(__file__).resolve().parents[1] / "images" / "portraits"

# Portrait configuration file path
PORTRAIT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "portrait_config.json"


class PortraitConfig:
    """Manages portrait configuration including external portrait folders."""
    
    def __init__(self):
        self.external_portrait_root: Optional[Path] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load portrait configuration from JSON file."""
        if not PORTRAIT_CONFIG_PATH.exists():
            return
        
        try:
            with open(PORTRAIT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                external_path = data.get('external_portrait_root')
                if external_path:
                    self.external_portrait_root = Path(external_path)
        except Exception:
            # If config is invalid, proceed with module-only behavior
            pass
    
    def save_config(self, external_root: Optional[Path]) -> None:
        """Save external portrait root to config file."""
        self.external_portrait_root = external_root
        
        # Ensure config directory exists
        PORTRAIT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        if external_root:
            data['external_portrait_root'] = str(external_root)
        
        try:
            with open(PORTRAIT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def get_search_paths(self) -> List[Path]:
        """Get list of portrait search paths in priority order."""
        paths = [PORTRAIT_BASE_PATH]
        if self.external_portrait_root and self.external_portrait_root.exists():
            paths.append(self.external_portrait_root)
        return paths


# Global portrait configuration instance
portrait_config = PortraitConfig()


class PortraitHelper:
    """Shared helper class for loading and displaying character portraits."""

    # Supported image extensions
    IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']

    @staticmethod
    def _extract_base_and_extension(filename: str) -> tuple[str, str]:
        """Extract base name and extension from filename.
        
        Returns:
            Tuple of (base_name, extension) e.g. ("MW_F_4", ".png")
        """
        path = Path(filename)
        return (path.stem, path.suffix.lower())

    @staticmethod
    def _find_portrait_variant(base_path: Path, category: str, filename: str, variant_suffix: str = "") -> Optional[Path]:
        """Find a portrait file with optional variant suffix.
        
        Args:
            base_path: Root path to search in
            category: Portrait category subdirectory (can be empty)
            filename: Original filename
            variant_suffix: Suffix to add before extension (e.g. "_cas")
            
        Returns:
            Path to portrait if found, None otherwise
        """
        base_name, original_ext = PortraitHelper._extract_base_and_extension(filename)
        
        # Build variant filename
        if variant_suffix:
            variant_base = f"{base_name}{variant_suffix}"
        else:
            variant_base = base_name
        
        # Try with category first
        if category:
            category_dir = base_path / category
            # Try original extension first
            if original_ext:
                portrait_path = category_dir / f"{variant_base}{original_ext}"
                if portrait_path.exists():
                    return portrait_path
            
            # Try other extensions
            for ext in PortraitHelper.IMAGE_EXTENSIONS:
                if ext != original_ext:
                    portrait_path = category_dir / f"{variant_base}{ext}"
                    if portrait_path.exists():
                        return portrait_path
        
        # Try without category
        # Try original extension first
        if original_ext:
            portrait_path = base_path / f"{variant_base}{original_ext}"
            if portrait_path.exists():
                return portrait_path
        
        # Try other extensions
        for ext in PortraitHelper.IMAGE_EXTENSIONS:
            if ext != original_ext:
                portrait_path = base_path / f"{variant_base}{ext}"
                if portrait_path.exists():
                    return portrait_path
        
        return None

    @staticmethod
    def resolve_portrait_path(character: Character, prefer_casual: bool = False) -> Optional[Path]:
        """Resolve the portrait path for a character.
        
        Args:
            character: Character object
            prefer_casual: If True, prefer _cas variant with fallback to default
            
        Returns:
            Path to the portrait file if found, None otherwise
        """
        if not character.portrait or not character.portrait.filename:
            return None

        category = character.portrait.category or ""
        filename = character.portrait.filename
        
        # Get all search paths
        search_paths = portrait_config.get_search_paths()
        
        # If prefer_casual, try casual variant first
        if prefer_casual:
            for base_path in search_paths:
                portrait_path = PortraitHelper._find_portrait_variant(
                    base_path, category, filename, "_cas"
                )
                if portrait_path:
                    return portrait_path
        
        # Try default (no suffix)
        for base_path in search_paths:
            portrait_path = PortraitHelper._find_portrait_variant(
                base_path, category, filename, ""
            )
            if portrait_path:
                return portrait_path

        return None

    @staticmethod
    def load_portrait_image(path: Path, max_size: tuple) -> Optional[object]:
        """Load and resize a portrait image.

        Args:
            path: Path to the image file
            max_size: Tuple (width, height) for maximum dimensions

        Returns:
            ImageTk.PhotoImage if successful, None on error
        """
        if not PIL_AVAILABLE:
            return None

        try:
            img = Image.open(path)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None


class CharacterDetailDialog:
    """
    Character Detail Window - "Character Sheet" UI with two-column layout.
    
    Left column: Portrait (bounded scaling) + essential identity + quick chips
    Right column: Scrollable accordion sections with pastel backgrounds
    
    Opened by right-clicking on a character in the tree view.
    """

    # Portrait size limits for detail dialog (bounded scaling, no cropping)
    MAX_PORTRAIT_WIDTH = 220
    MAX_PORTRAIT_HEIGHT = 300

    # Attribute section layout threshold
    MULTI_COLUMN_THRESHOLD = 4  # Use 2 columns when attributes >= this value

    # Pastel background colors for accordion sections
    COLORS = {
        "overview": "#F6F4EF",      # warm sand
        "attributes": "#F2F7FF",    # pale blue
        "skills": "#F2FFF6",        # pale mint
        "personality": "#F6F2FF",   # pale lavender
        "relationships": "#FFF4F2", # pale peach
        "equipment": "#F7F7F7",     # neutral light gray
    }

    def __init__(self, parent: tk.Tk, character: Character, current_date: date, 
                 character_lookup: Optional[Dict[str, Character]] = None) -> None:
        self.parent = parent
        self.character = character
        self.current_date = current_date
        self.character_lookup = character_lookup or {}  # For resolving relationship partner names
        self.portrait_image = None  # Keep reference to prevent garbage collection
        self.custom_portrait_path: Optional[Path] = None

        # Create dialog window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Character Sheet: {character.name}")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        self.window.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the main two-column layout."""
        main_frame = tk.Frame(self.window, bg="#FFFFFF")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create horizontal layout: left (fixed) + right (scrollable)
        # Left column: Portrait + Identity + Quick Chips (fixed width ~280px)
        left_frame = tk.Frame(main_frame, bg="#FFFFFF", width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        left_frame.pack_propagate(False)  # Maintain fixed width

        # Right column: Accordion sections (scrollable, expands to fill)
        right_frame = tk.Frame(main_frame, bg="#FFFFFF")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._build_left_panel(left_frame)
        self._build_right_panel(right_frame)

    def _build_left_panel(self, parent: tk.Frame) -> None:
        """Build the left panel: Portrait + Identity + Quick Chips."""
        char = self.character

        # --- Portrait Section ---
        portrait_frame = tk.Frame(parent, bg="#FFFFFF")
        portrait_frame.pack(fill=tk.X, pady=(0, 12))

        self.portrait_label = tk.Label(portrait_frame, text="No portrait", bg="#E0E0E0", 
                                       width=200, height=320, anchor="center")
        self.portrait_label.pack(pady=5)

        # Try to load portrait (prefer _cas variant)
        self._load_portrait()

        # Select portrait button
        btn_portrait = tk.Button(portrait_frame, text="Select Portrait...", 
                                 command=self._select_portrait, bg="#DDDDDD", relief=tk.FLAT)
        btn_portrait.pack(pady=5)

        # --- Identity Block ---
        identity_frame = tk.Frame(parent, bg="#FFFFFF")
        identity_frame.pack(fill=tk.X, pady=(0, 12))

        # Compact identity labels
        identity_data = [
            ("Name:", char.name),
            ("Callsign:", char.callsign or "—"),
            ("Rank:", char.rank_name or char.rank or "—"),
            ("Unit:", char.unit.unit_name if char.unit else "—"),
            ("Force:", char.unit.force_name if char.unit else "—"),
            ("Primary:", char.profession or "—"),
            ("Secondary:", char.secondary_profession or "—"),
        ]

        for label_text, value_text in identity_data:
            row = tk.Frame(identity_frame, bg="#FFFFFF")
            row.pack(fill=tk.X, pady=1)
            
            lbl = tk.Label(row, text=label_text, bg="#FFFFFF", fg="#1E1E1E",
                          font=("TkDefaultFont", 9, "bold"), anchor="w", width=10)
            lbl.pack(side=tk.LEFT, padx=(0, 5))
            
            val = tk.Label(row, text=value_text, bg="#FFFFFF", fg="#1E1E1E",
                          font=("TkDefaultFont", 9), anchor="w")
            val.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # --- Quick Chips Strip ---
        chips_frame = tk.Frame(parent, bg="#FFFFFF")
        chips_frame.pack(fill=tk.X, pady=(12, 0))

        chips_title = tk.Label(chips_frame, text="Quick Info", bg="#FFFFFF", fg="#1E1E1E",
                              font=("TkDefaultFont", 10, "bold"))
        chips_title.pack(anchor="w", pady=(0, 5))

        # Gunnery/Piloting chips
        if char.skills:
            gunnery = char.skills.get("Gunnery") or char.skills.get("Gunnery/Mek") or char.skills.get("Mek Gunnery")
            piloting = char.skills.get("Piloting") or char.skills.get("Piloting/Mek") or char.skills.get("Mek Piloting")
            
            if gunnery or piloting:
                skill_row = tk.Frame(chips_frame, bg="#FFFFFF")
                skill_row.pack(fill=tk.X, pady=2)
                
                if gunnery:
                    self._create_chip(skill_row, f"Gunnery: {gunnery}", "#D4E6F1")
                if piloting:
                    self._create_chip(skill_row, f"Piloting: {piloting}", "#D5F4E6")

        # Trait count chip
        trait_count = len([t for t in char.traits.values() if "NONE" not in str(t).upper()])
        if trait_count > 0:
            chip_row = tk.Frame(chips_frame, bg="#FFFFFF")
            chip_row.pack(fill=tk.X, pady=2)
            self._create_chip(chip_row, f"{trait_count} Traits", "#E8DAEF")

        # Quirks count chip
        if char.quirks:
            chip_row = tk.Frame(chips_frame, bg="#FFFFFF")
            chip_row.pack(fill=tk.X, pady=2)
            self._create_chip(chip_row, f"{len(char.quirks)} Quirks", "#FADBD8")

        # SPAs count chip
        if char.abilities:
            chip_row = tk.Frame(chips_frame, bg="#FFFFFF")
            chip_row.pack(fill=tk.X, pady=2)
            self._create_chip(chip_row, f"{len(char.abilities)} SPAs", "#FCF3CF")

    def _create_chip(self, parent: tk.Frame, text: str, bg_color: str) -> None:
        """Create a small colored chip label."""
        chip = tk.Label(parent, text=text, bg=bg_color, fg="#1E1E1E",
                       font=("TkDefaultFont", 8), padx=6, pady=2, relief=tk.FLAT)
        chip.pack(side=tk.LEFT, padx=2)

    def _build_right_panel(self, parent: tk.Frame) -> None:
        """Build the right panel: Scrollable accordion sections."""
        # Create scrollable canvas
        canvas = tk.Canvas(parent, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#FFFFFF")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create accordion container
        accordion = AccordionContainer(scrollable_frame, single_open=True)
        accordion.pack(fill=tk.BOTH, expand=True)

        # Add sections in order
        self._build_overview_section(accordion)
        self._build_progress_section(accordion)  # Phase 3: Event-driven state
        self._build_attributes_section(accordion)
        self._build_skills_section(accordion)
        self._build_personality_section(accordion)
        self._build_relationships_section(accordion)
        self._build_equipment_section(accordion)

    def _build_overview_section(self, accordion: AccordionContainer) -> None:
        """Overview section (default open)."""
        section = accordion.add_section("Overview", self.COLORS["overview"], is_open=True)
        body = section.get_body()

        char = self.character

        # Two-column mini-layout
        left_col = tk.Frame(body, bg=self.COLORS["overview"])
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        right_col = tk.Frame(body, bg=self.COLORS["overview"])
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Left: Summary fields
        summary_data = [
            ("Rank:", char.rank_name or char.rank or "—"),
            ("Age:", f"{char.age} ({char.age_group})"),
            ("Birthday:", char.birthday.strftime("%Y-%m-%d") if char.birthday else "—"),
            ("Primary Role:", char.profession or "—"),
            ("Secondary Role:", char.secondary_profession or "—"),
        ]

        if char.unit:
            summary_data.append(("Unit:", char.unit.unit_name))
            summary_data.append(("Formation:", char.unit.formation_level or "—"))
            summary_data.append(("Crew Role:", char.unit.crew_role or "—"))

        for label_text, value_text in summary_data:
            row = tk.Frame(left_col, bg=self.COLORS["overview"])
            row.pack(fill=tk.X, pady=2)
            
            lbl = tk.Label(row, text=label_text, bg=self.COLORS["overview"], fg="#1E1E1E",
                          font=("TkDefaultFont", 9, "bold"), anchor="w", width=14)
            lbl.pack(side=tk.LEFT)
            
            val = tk.Label(row, text=value_text, bg=self.COLORS["overview"], fg="#1E1E1E",
                          font=("TkDefaultFont", 9), anchor="w")
            val.pack(side=tk.LEFT)

        # Right: Highlights
        highlights_title = tk.Label(right_col, text="Highlights", bg=self.COLORS["overview"],
                                    fg="#1E1E1E", font=("TkDefaultFont", 10, "bold"))
        highlights_title.pack(anchor="w", pady=(0, 5))

        # Top skills (top 5 by level)
        if char.skills:
            sorted_skills = sorted(char.skills.items(), key=lambda x: -x[1])[:5]
            skills_label = tk.Label(right_col, text="Top Skills:", bg=self.COLORS["overview"],
                                   fg="#1E1E1E", font=("TkDefaultFont", 9, "bold"))
            skills_label.pack(anchor="w", pady=(5, 2))
            
            for skill_name, level in sorted_skills:
                skill_line = tk.Label(right_col, text=f"• {skill_name}: {level}",
                                     bg=self.COLORS["overview"], fg="#1E1E1E",
                                     font=("TkDefaultFont", 9))
                skill_line.pack(anchor="w", padx=(10, 0))

        # SPAs preview
        if char.abilities:
            spa_label = tk.Label(right_col, text=f"Special Abilities ({len(char.abilities)}):",
                                bg=self.COLORS["overview"], fg="#1E1E1E",
                                font=("TkDefaultFont", 9, "bold"))
            spa_label.pack(anchor="w", pady=(5, 2))
            
            for spa_name in list(char.abilities.keys())[:3]:
                spa_line = tk.Label(right_col, text=f"• {spa_name}",
                                   bg=self.COLORS["overview"], fg="#1E1E1E",
                                   font=("TkDefaultFont", 9))
                spa_line.pack(anchor="w", padx=(10, 0))

        # Quirks preview
        if char.quirks:
            quirk_label = tk.Label(right_col, text=f"Quirks ({len(char.quirks)}):",
                                  bg=self.COLORS["overview"], fg="#1E1E1E",
                                  font=("TkDefaultFont", 9, "bold"))
            quirk_label.pack(anchor="w", pady=(5, 2))
            
            for quirk in char.quirks[:3]:
                quirk_display = quirk.replace("_", " ").title()
                quirk_line = tk.Label(right_col, text=f"• {quirk_display}",
                                     bg=self.COLORS["overview"], fg="#1E1E1E",
                                     font=("TkDefaultFont", 9))
                quirk_line.pack(anchor="w", padx=(10, 0))

    def _build_progress_section(self, accordion: AccordionContainer) -> None:
        """
        Progress section - Event-driven character state (Phase 3).
        
        Displays:
        - XP (numeric)
        - Confidence (bar, amber #FFB300)
        - Fatigue (bar, orange #FB8C00)
        - Reputation Pool (bar, violet #8E24AA)
        
        All values are READ-ONLY and modified only by event outcomes.
        """
        # Use a light yellow/cream background for progress
        progress_color = "#FFFAF0"
        section = accordion.add_section("Progress", progress_color, is_open=False)
        body = section.get_body()
        
        char = self.character
        
        # Title
        title_label = tk.Label(body, text="Event-Driven Progress",
                              bg=progress_color, fg="#1E1E1E",
                              font=("TkDefaultFont", 10, "bold"))
        title_label.pack(anchor="w", pady=(0, 8))
        
        # XP (numeric only, no bar)
        xp_frame = tk.Frame(body, bg=progress_color)
        xp_frame.pack(fill=tk.X, pady=4)
        
        xp_label = tk.Label(xp_frame, text="XP:", bg=progress_color, fg="#1E1E1E",
                           font=("TkDefaultFont", 9, "bold"), anchor="w", width=16)
        xp_label.pack(side=tk.LEFT)
        
        xp_value = tk.Label(xp_frame, text=str(char.xp), bg=progress_color, fg="#1E1E1E",
                           font=("TkDefaultFont", 9), anchor="w")
        xp_value.pack(side=tk.LEFT)
        
        # Helper function to create progress bars
        def create_progress_bar(parent, label_text: str, value: int, max_value: int, color: str):
            """Create a labeled progress bar."""
            frame = tk.Frame(parent, bg=progress_color)
            frame.pack(fill=tk.X, pady=4)
            
            # Label
            label = tk.Label(frame, text=label_text, bg=progress_color, fg="#1E1E1E",
                           font=("TkDefaultFont", 9, "bold"), anchor="w", width=16)
            label.pack(side=tk.LEFT)
            
            # Bar container
            bar_container = tk.Frame(frame, bg=progress_color)
            bar_container.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            # Progress bar (canvas-based)
            canvas = tk.Canvas(bar_container, height=16, bg="#E0E0E0", 
                             highlightthickness=0, relief=tk.FLAT)
            canvas.pack(fill=tk.X)
            
            # Draw filled portion
            canvas_width = 200  # Fixed width for consistency
            filled_width = int((value / max_value) * canvas_width)
            canvas.config(width=canvas_width)
            canvas.create_rectangle(0, 0, filled_width, 16, fill=color, outline="")
            
            # Value text
            value_text = tk.Label(frame, text=f"{value}/{max_value}", bg=progress_color,
                                fg="#1E1E1E", font=("TkDefaultFont", 8), width=8)
            value_text.pack(side=tk.LEFT)
        
        # Confidence bar (Amber/Gold #FFB300)
        create_progress_bar(body, "Confidence:", char.confidence, 100, "#FFB300")
        
        # Fatigue bar (Orange #FB8C00)
        create_progress_bar(body, "Fatigue:", char.fatigue, 100, "#FB8C00")
        
        # Reputation Pool bar (Violet #8E24AA)
        create_progress_bar(body, "Reputation Pool:", char.reputation_pool, 100, "#8E24AA")
        
        # Info note
        info_label = tk.Label(body, 
                             text="ℹ️ These values are modified by event outcomes only.",
                             bg=progress_color, fg="#666666",
                             font=("TkDefaultFont", 8, "italic"), anchor="w")
        info_label.pack(anchor="w", pady=(8, 0))

    def _build_attributes_section(self, accordion: AccordionContainer) -> None:
        """Attributes section (numeric values only) with multi-column layout."""
        section = accordion.add_section("Attributes", self.COLORS["attributes"], is_open=False)
        body = section.get_body()

        char = self.character

        if not char.attributes:
            no_data = tk.Label(body, text="No attribute data available.",
                              bg=self.COLORS["attributes"], fg="#1E1E1E")
            no_data.pack(pady=10)
            return

        # Multi-column grid layout for attributes
        # Use 2 columns for 4+ attributes, 1 column for fewer
        sorted_attrs = sorted(char.attributes.items())
        num_attrs = len(sorted_attrs)
        
        # Determine column count based on threshold
        num_columns = 2 if num_attrs >= self.MULTI_COLUMN_THRESHOLD else 1
        
        # Create a grid container
        grid_frame = tk.Frame(body, bg=self.COLORS["attributes"])
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configure columns to expand evenly
        for col in range(num_columns):
            grid_frame.grid_columnconfigure(col, weight=1, uniform="attr_col")
        
        # Place attributes in grid
        for idx, (attr_name, attr_value) in enumerate(sorted_attrs):
            row = idx // num_columns
            col = idx % num_columns
            
            # Create frame for this attribute
            attr_frame = tk.Frame(grid_frame, bg=self.COLORS["attributes"])
            attr_frame.grid(row=row, column=col, sticky="ew", padx=5, pady=2)
            
            # Attribute label
            lbl = tk.Label(attr_frame, text=f"{attr_name}:", bg=self.COLORS["attributes"],
                          fg="#1E1E1E", font=("TkDefaultFont", 9, "bold"), width=12, anchor="w")
            lbl.pack(side=tk.LEFT, padx=(0, 10))
            
            # Attribute value
            val = tk.Label(attr_frame, text=str(attr_value), bg=self.COLORS["attributes"],
                          fg="#1E1E1E", font=("TkDefaultFont", 9), anchor="w")
            val.pack(side=tk.LEFT)

    def _build_skills_section(self, accordion: AccordionContainer) -> None:
        """Skills section with search and attribute support hints."""
        section = accordion.add_section("Skills", self.COLORS["skills"], is_open=False)
        body = section.get_body()

        char = self.character

        if not char.skills:
            no_data = tk.Label(body, text="No skill data available.",
                              bg=self.COLORS["skills"], fg="#1E1E1E")
            no_data.pack(pady=10)
            return

        # Search box
        search_frame = tk.Frame(body, bg=self.COLORS["skills"])
        search_frame.pack(fill=tk.X, pady=(0, 10))

        search_label = tk.Label(search_frame, text="Search:", bg=self.COLORS["skills"],
                               fg="#1E1E1E", font=("TkDefaultFont", 9))
        search_label.pack(side=tk.LEFT, padx=(0, 5))

        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Skills container (will be filtered by search)
        skills_container = tk.Frame(body, bg=self.COLORS["skills"])
        skills_container.pack(fill=tk.BOTH, expand=True)

        def update_skills_display(*args):
            """Update skills display based on search."""
            # Clear container
            for widget in skills_container.winfo_children():
                widget.destroy()

            search_text = search_var.get().lower()
            
            # Sort skills by name
            sorted_skills = sorted(char.skills.items(), key=lambda x: x[0])
            
            for skill_name, skill_level in sorted_skills:
                # Filter by search
                if search_text and search_text not in skill_name.lower():
                    continue

                skill_row = tk.Frame(skills_container, bg=self.COLORS["skills"])
                skill_row.pack(fill=tk.X, pady=3)

                # Skill name and level
                skill_label = tk.Label(skill_row, text=f"{skill_name} — {skill_level}",
                                      bg=self.COLORS["skills"], fg="#1E1E1E",
                                      font=("TkDefaultFont", 9, "bold"), anchor="w")
                skill_label.pack(anchor="w")

                # Attribute support hint (italic, smaller)
                support_text = format_skill_support(skill_name)
                if support_text:
                    support_label = tk.Label(skill_row, text=support_text,
                                           bg=self.COLORS["skills"], fg="#555555",
                                           font=("TkDefaultFont", 8, "italic"), anchor="w")
                    support_label.pack(anchor="w", padx=(15, 0))

        # Bind search
        search_var.trace("w", update_skills_display)
        
        # Initial display
        update_skills_display()

    def _build_personality_section(self, accordion: AccordionContainer) -> None:
        """Personality section with subsections: Traits / Quirks / SPAs."""
        section = accordion.add_section("Personality", self.COLORS["personality"], is_open=False)
        body = section.get_body()

        char = self.character

        # Create sub-notebook for Traits / Quirks / SPAs
        sub_notebook = ttk.Notebook(body)
        sub_notebook.pack(fill=tk.BOTH, expand=True)

        # --- Traits Tab ---
        traits_tab = tk.Frame(sub_notebook, bg=self.COLORS["personality"])
        sub_notebook.add(traits_tab, text="Traits")

        if char.traits:
            trait_enums = get_character_traits_as_enums(char)
            for category, enum_str in sorted(trait_enums.items()):
                if ":" in enum_str:
                    _, trait_key = enum_str.split(":", 1)
                else:
                    trait_key = enum_str

                row = tk.Frame(traits_tab, bg=self.COLORS["personality"])
                row.pack(fill=tk.X, pady=3, padx=10)

                lbl = tk.Label(row, text=f"{category}:", bg=self.COLORS["personality"],
                              fg="#1E1E1E", font=("TkDefaultFont", 9, "bold"), width=12, anchor="w")
                lbl.pack(side=tk.LEFT)

                val = tk.Label(row, text=trait_key, bg=self.COLORS["personality"],
                              fg="#1E1E1E", font=("TkDefaultFont", 9), anchor="w")
                val.pack(side=tk.LEFT)
        else:
            no_traits = tk.Label(traits_tab, text="No personality traits available.",
                                bg=self.COLORS["personality"], fg="#1E1E1E")
            no_traits.pack(pady=10)

        # --- Quirks Tab ---
        quirks_tab = tk.Frame(sub_notebook, bg=self.COLORS["personality"])
        sub_notebook.add(quirks_tab, text="Quirks")

        if char.quirks:
            quirk_container = tk.Frame(quirks_tab, bg=self.COLORS["personality"])
            quirk_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            for quirk in sorted(char.quirks):
                quirk_display = quirk.replace("_", " ").title()
                
                # Create chip-style badge
                chip_frame = tk.Frame(quirk_container, bg=self.COLORS["personality"])
                chip_frame.pack(fill=tk.X, pady=2)

                chip = tk.Label(chip_frame, text=quirk_display, bg="#FADBD8", fg="#1E1E1E",
                               font=("TkDefaultFont", 9), padx=8, pady=4, relief=tk.RAISED)
                chip.pack(side=tk.LEFT)
        else:
            no_quirks = tk.Label(quirks_tab, text="No quirks available.",
                                bg=self.COLORS["personality"], fg="#1E1E1E")
            no_quirks.pack(pady=10)

        # --- Special Abilities Tab ---
        spa_tab = tk.Frame(sub_notebook, bg=self.COLORS["personality"])
        sub_notebook.add(spa_tab, text="Special Abilities")

        if char.abilities:
            spa_container = tk.Frame(spa_tab, bg=self.COLORS["personality"])
            spa_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            for spa_name, spa_desc in sorted(char.abilities.items()):
                spa_frame = tk.Frame(spa_container, bg=self.COLORS["personality"])
                spa_frame.pack(fill=tk.X, pady=4)

                # SPA name (bold)
                name_label = tk.Label(spa_frame, text=spa_name, bg=self.COLORS["personality"],
                                     fg="#1E1E1E", font=("TkDefaultFont", 9, "bold"), anchor="w")
                name_label.pack(anchor="w")

                # SPA description (smaller, italic)
                if spa_desc:
                    desc_label = tk.Label(spa_frame, text=spa_desc, bg=self.COLORS["personality"],
                                         fg="#555555", font=("TkDefaultFont", 8, "italic"),
                                         anchor="w", wraplength=400, justify=tk.LEFT)
                    desc_label.pack(anchor="w", padx=(15, 0))
        else:
            no_spa = tk.Label(spa_tab, text="None", bg=self.COLORS["personality"], fg="#1E1E1E")
            no_spa.pack(pady=10)

    def _build_relationships_section(self, accordion: AccordionContainer) -> None:
        """
        Relationships section - NEW SOCIAL RELATIONSHIP SYSTEM.
        
        CRITICAL: This section now displays data from the new relationship runtime provider.
        The legacy friendship dict system is OBSOLETE and NO LONGER USED.
        """
        section = accordion.add_section("Relationships", self.COLORS["relationships"], is_open=False)
        body = section.get_body()

        char = self.character

        # Initialize relationship runtime adapter
        # Note: campaign_start_date is not available, so we use current_date as fallback
        # This will need to be updated when campaign metadata includes start date
        adapter = RelationshipRuntimeAdapter(
            current_date=self.current_date,
            campaign_start_date=self.current_date  # TODO: Use actual campaign start date when available
        )

        # Get relationships for this character from the runtime provider
        relationships = adapter.get_relationships_for_character(char.id)

        if not relationships:
            no_data = tk.Label(body, text="No relationships yet.",
                              bg=self.COLORS["relationships"], fg="#1E1E1E",
                              font=("TkDefaultFont", 10))
            no_data.pack(pady=20)
            return

        # Relationships container (scrollable if many relationships)
        rel_container = tk.Frame(body, bg=self.COLORS["relationships"])
        rel_container.pack(fill=tk.BOTH, expand=True, pady=5)

        # Display each relationship as a compact row
        for rel in relationships:
            self._build_relationship_row(rel_container, rel, adapter)

    def _build_relationship_row(self, parent: tk.Frame, relationship: Dict[str, Any],
                                adapter: RelationshipRuntimeAdapter) -> None:
        """
        Build a single relationship overview row.
        Shows: Partner name | Axes indicators | Status | Details button
        """
        char = self.character
        
        # Get the other character's ID
        other_id = adapter.get_other_character_id(relationship, char.id)
        
        # Resolve partner name
        if self.character_lookup and other_id in self.character_lookup:
            other_char = self.character_lookup[other_id]
            partner_name = other_char.name
        else:
            partner_name = f"ID: {other_id[:12]}..."

        # Row frame
        row = tk.Frame(parent, bg=self.COLORS["relationships"], relief=tk.FLAT, borderwidth=1)
        row.pack(fill=tk.X, pady=3, padx=5)

        # Partner name
        name_label = tk.Label(row, text=partner_name,
                             bg=self.COLORS["relationships"], fg="#1E1E1E",
                             font=("TkDefaultFont", 10), width=20, anchor="w")
        name_label.pack(side=tk.LEFT, padx=(5, 10))

        # Axes indicators (compact)
        axes = relationship.get("axes", {})
        
        # Friendship indicator
        friendship = axes.get("friendship", 0)
        self._create_axis_chip(row, "F", friendship)
        
        # Romance indicator
        romance = axes.get("romance", 0)
        self._create_axis_chip(row, "R", romance)
        
        # Respect indicator
        respect = axes.get("respect", 0)
        self._create_axis_chip(row, "E", respect)  # E for Esteem/Respect

        # Derived status labels (1-2 most relevant)
        derived = relationship.get("derived", {})
        states = derived.get("states", {})
        
        if states:
            # Show friendship state as primary status
            friendship_state = states.get("friendship", "")
            if friendship_state and friendship_state != "neutral":
                status_label = tk.Label(row, text=friendship_state.replace("_", " ").title(),
                                       bg=self.COLORS["relationships"], fg="#555555",
                                       font=("TkDefaultFont", 9, "italic"))
                status_label.pack(side=tk.LEFT, padx=5)

        # Spacer
        tk.Frame(row, bg=self.COLORS["relationships"]).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Details button
        def show_details():
            self._show_relationship_detail(relationship, other_id)

        details_btn = tk.Button(row, text="Details...",
                               command=show_details,
                               bg="#DDDDDD", relief=tk.FLAT,
                               font=("TkDefaultFont", 8),
                               padx=8, pady=2)
        details_btn.pack(side=tk.RIGHT, padx=5)

    def _create_axis_chip(self, parent: tk.Frame, label: str, value: int) -> None:
        """
        Create a compact axis indicator chip.
        Shows: Label (F/R/E) with color-coded value.
        """
        # Determine color based on value
        if value > 50:
            bg_color = "#C8E6C9"  # Light green
            fg_color = "#2E7D32"  # Dark green
        elif value > 20:
            bg_color = "#E8F5E9"  # Pale green
            fg_color = "#66BB6A"  # Medium green
        elif value > -20:
            bg_color = "#F5F5F5"  # Gray
            fg_color = "#757575"  # Gray text
        elif value > -50:
            bg_color = "#FFCDD2"  # Pale red
            fg_color = "#EF5350"  # Medium red
        else:
            bg_color = "#FFCDD2"  # Light red
            fg_color = "#C62828"  # Dark red

        # Format value
        value_str = f"+{value}" if value > 0 else str(value)
        
        chip_text = f"{label}:{value_str}"
        
        chip = tk.Label(parent, text=chip_text,
                       bg=bg_color, fg=fg_color,
                       font=("TkDefaultFont", 8, "bold"),
                       padx=4, pady=2, relief=tk.FLAT)
        chip.pack(side=tk.LEFT, padx=2)

    def _show_relationship_detail(self, relationship: Dict[str, Any], other_id: str) -> None:
        """
        Open the relationship detail dialog for a specific relationship.
        """
        char = self.character
        
        # Get the other character
        if self.character_lookup and other_id in self.character_lookup:
            other_char = self.character_lookup[other_id]
        else:
            messagebox.showwarning(
                "Character Not Found",
                f"Cannot display details: Character {other_id} not in loaded data."
            )
            return

        # Open detail dialog
        RelationshipDetailDialog(self.window, relationship, char, other_char)

    def _build_equipment_section(self, accordion: AccordionContainer) -> None:
        """Equipment section (disabled scaffold placeholder)."""
        section = accordion.add_section("Equipment", self.COLORS["equipment"], is_open=False)
        body = section.get_body()

        # Placeholder note
        note = tk.Label(body, text="Equipment will be implemented later.",
                       bg=self.COLORS["equipment"], fg="#888888",
                       font=("TkDefaultFont", 9, "italic"))
        note.pack(pady=10)

        # Disabled table scaffold
        table_frame = tk.Frame(body, bg=self.COLORS["equipment"])
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Headers
        headers = ["Item", "Qty", "Notes"]
        for i, header in enumerate(headers):
            header_label = tk.Label(table_frame, text=header, bg="#D0D0D0", fg="#1E1E1E",
                                   font=("TkDefaultFont", 9, "bold"), relief=tk.RIDGE,
                                   width=15 if i == 0 else 10)
            header_label.grid(row=0, column=i, sticky="ew", padx=1, pady=1)

        # Placeholder row
        placeholder_data = [("—", "—", "—")]
        for row_idx, (item, qty, notes) in enumerate(placeholder_data, start=1):
            for col_idx, value in enumerate([item, qty, notes]):
                cell = tk.Label(table_frame, text=value, bg="#F0F0F0", fg="#AAAAAA",
                               font=("TkDefaultFont", 9), relief=tk.RIDGE,
                               width=15 if col_idx == 0 else 10)
                cell.grid(row=row_idx, column=col_idx, sticky="ew", padx=1, pady=1)

        # Disabled buttons
        btn_frame = tk.Frame(body, bg=self.COLORS["equipment"])
        btn_frame.pack(fill=tk.X, pady=10)

        for btn_text in ["Add", "Remove", "Import"]:
            btn = tk.Button(btn_frame, text=btn_text, state=tk.DISABLED, bg="#CCCCCC")
            btn.pack(side=tk.LEFT, padx=5)

    def _load_portrait(self) -> None:
        """Attempt to automatically load the character's portrait (prefer casual variant)."""
        if not PIL_AVAILABLE:
            self.portrait_label.config(text="PIL not available\nfor image loading")
            return

        char = self.character
        # Prefer casual variant (_cas) for detail dialog
        portrait_path = PortraitHelper.resolve_portrait_path(char, prefer_casual=True)

        if portrait_path is None:
            if not char.portrait or not char.portrait.filename:
                self.portrait_label.config(text="No portrait\ndata available")
            else:
                category = char.portrait.category or ""
                filename = char.portrait.filename
                full_path = f"{category}/{filename}" if category else filename
                self.portrait_label.config(text=f"Portrait not found:\n{full_path}")
            return

        self._display_portrait(portrait_path)

    def _load_portrait_bounded(self, path: Path) -> Optional[object]:
        """
        Load and scale a portrait image using bounded scaling (NO cropping).
        
        This method implements the required scaling algorithm:
        - Keeps original aspect ratio
        - Scales as large as possible within MAX_PORTRAIT_WIDTH x MAX_PORTRAIT_HEIGHT
        - Never exceeds defined maximum dimensions
        - No cropping, no distortion
        - Does not upscale images smaller than the limits
        
        Args:
            path: Path to the image file
            
        Returns:
            ImageTk.PhotoImage if successful, None on error
        """
        if not PIL_AVAILABLE:
            return None
        
        try:
            # Load image at original resolution
            img = Image.open(path)
            w, h = img.size
            
            # Compute scaling factors
            scale_w = self.MAX_PORTRAIT_WIDTH / w
            scale_h = self.MAX_PORTRAIT_HEIGHT / h
            scale = min(scale_w, scale_h, 1.0)  # Never upscale (scale > 1.0)
            
            # Compute new size
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            # Resize using LANCZOS resampling (high quality)
            resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            return ImageTk.PhotoImage(resized_img)
        except Exception:
            return None

    def _display_portrait(self, path: Path) -> None:
        """Display a portrait image from the given path using bounded scaling."""
        photo_image = self._load_portrait_bounded(path)
        if photo_image:
            self.portrait_image = photo_image
            self.portrait_label.config(image=self.portrait_image, text="", bg="#FFFFFF")
        else:
            self.portrait_label.config(text="Error loading\nimage")

    def _select_portrait(self) -> None:
        """Open file dialog to select a custom portrait."""
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("All files", "*.*")
        ]
        path = filedialog.askopenfilename(
            parent=self.window,
            title="Select Portrait Image",
            filetypes=filetypes
        )
        if path:
            self.custom_portrait_path = Path(path)
            self._display_portrait(self.custom_portrait_path)


class MekSocialGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("MekHQ Social Simulator")
        self.master.geometry("1200x800")

        self.characters: Dict[str, Character] = {}
        self.current_day: int = 1
        self.selected_character_id: Optional[str] = None

        # Real-world date and event manager
        self.current_date: date = date.today()
        self.event_manager = EventManager() if EventManager is not None else None

        # Log popup state (kept for compatibility with import/export logging)
        self.log_window = None
        self.log_text = None

        self._build_menu_bar()
        self._build_widgets()

    # --- GUI construction -------------------------------------------------

    def _build_menu_bar(self) -> None:
        """Build the menu bar at the top of the window."""
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Export submenu
        export_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Export", menu=export_menu)
        
        export_menu.add_command(
            label="Export Campaign Data from .cpnx...",
            command=self._export_campaign_data
        )
        
        # Import submenu
        import_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Import", menu=import_menu)
        
        import_menu.add_command(
            label="Import Campaign Meta (Date & Rank System)...",
            command=self._import_campaign_meta
        )
        import_menu.add_separator()
        import_menu.add_command(
            label="Import Personnel (JSON)...",
            command=self._import_personnel
        )
        import_menu.add_command(
            label="Import TO&E (JSON)...",
            command=self._import_toe
        )
        import_menu.add_separator()
        import_menu.add_command(
            label="Set External Portrait Folder...",
            command=self._set_external_portrait_folder
        )
        
        # Exit option
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

    def _build_widgets(self) -> None:
        """Build the main 4-region layout: Top Bar, Left Nav, Right Inspector, Bottom Feed."""
        # Main container with dark background
        main_container = ttk.Frame(self.master, style="Main.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure root background
        self.master.configure(bg=THEME["bg_main"])
        
        # Build 4-region layout
        self._build_top_bar(main_container)
        self._build_middle_section(main_container)
        self._build_bottom_feed(main_container)

    def _build_top_bar(self, parent: ttk.Frame) -> None:
        """Build top bar: Campaign Day + Calendar access + Calendar Widget (fixed height ~36px)."""
        top_bar = ttk.Frame(parent, style="Panel.TFrame", height=36)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)  # Fixed height
        
        # Campaign Day display (clickable for date picker)
        self.date_label = ttk.Label(
            top_bar, 
            text="", 
            style="Primary.TLabel",
            padding=(8, 6)
        )
        self.date_label.pack(side=tk.LEFT, padx=4)
        self.date_label.bind("<Button-1>", self._on_date_left_click)
        self.date_label.bind("<Button-3>", self._on_date_right_click)
        self._update_date_display()
        
        # Next day button
        next_day_btn = ttk.Button(
            top_bar, 
            text="Next Day", 
            command=self._next_day,
            style="Primary.TButton"
        )
        next_day_btn.pack(side=tk.LEFT, padx=4)
        
        # Calendar button
        if DetailedCalendarWindow is not None:
            calendar_btn = ttk.Button(
                top_bar,
                text="📅 Calendar",
                command=self._open_calendar,
                style="Primary.TButton"
            )
            calendar_btn.pack(side=tk.LEFT, padx=4)
        
        # Calendar Widget (compact, right-aligned)
        # This makes the calendar visibly accessible in the UI
        if EventManager is not None:
            try:
                from merk_calendar.widget import CalendarWidget
                
                self.calendar_widget = CalendarWidget(
                    top_bar,
                    event_manager=self.event_manager,
                    initial_date=self.current_date,
                    on_date_change=self._on_calendar_date_change,
                    bg=THEME["bg_panel"]
                )
                self.calendar_widget.pack(side=tk.RIGHT, padx=8, pady=2)
            except Exception as e:
                print(f"[WARNING] Could not create calendar widget: {e}")
    
    def _on_calendar_date_change(self, new_date: date) -> None:
        """
        Handle date change from calendar widget.
        
        Args:
            new_date: New date selected in calendar widget
        """
        # Update current date
        self.current_date = new_date
        
        # Update day counter (calculate days from some baseline)
        # For now, we'll just keep the current day and update the date display
        self._update_date_display()
        
        # Update character ages
        self._update_character_ages()
        
        # Execute any events scheduled for this date
        if self.event_manager and self.characters:
            logs = self.event_manager.execute_events_for_date(new_date, self.characters)
            if logs:
                self._log_to_feed(f"Executed {len(logs)} event(s) for {new_date.strftime('%Y-%m-%d')}")
                for log in logs:
                    self._log_to_feed(f"  • {log.event_name} (ID:{log.event_id})")
        
        # Update displays
        self._update_day_events_bar()
        self._update_day_events_description()
        
        # Refresh details if a character is selected
        if self.selected_character_id and self.selected_character_id in self.characters:
            self._update_details(self.characters[self.selected_character_id])
    
    def _build_middle_section(self, parent: ttk.Frame) -> None:
        """Build middle section: Left Navigation Pane + Right Inspector Panel."""
        middle_pane = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        middle_pane.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # Left Navigation Pane (20-25% width, min 220px)
        self._build_left_navigation(middle_pane)
        
        # Right Inspector Panel (75-80% width)
        self._build_inspector_panel(middle_pane)
    
    def _build_left_navigation(self, parent: ttk.PanedWindow) -> None:
        """Build left navigation pane: TreeView only."""
        left_frame = ttk.Frame(parent, style="Panel.TFrame", width=250)
        parent.add(left_frame, weight=1)
        
        # TreeView with scrollbar
        self.tree = ttk.Treeview(left_frame, columns=("type",), show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Button-3>", self._on_tree_right_click)
        
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Initialize tree nodes
        self.root_node = self.tree.insert("", "end", text="Personnel", open=True)
        self.no_toe_node = self.tree.insert(self.root_node, "end", text="No TO&E", open=True)
    
    def _build_inspector_panel(self, parent: ttk.PanedWindow) -> None:
        """Build right inspector panel: Context Header + Primary Block + Secondary Block + Utility Strip."""
        inspector_frame = ttk.Frame(parent, style="Panel.TFrame")
        parent.add(inspector_frame, weight=3)
        
        # Step 1: Build context header container
        self._build_context_header(inspector_frame)
        
        # Step 2: Build content frame for Primary and Secondary blocks
        content_frame = ttk.Frame(inspector_frame, style="Panel.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        # Step 3: Build primary container (structure only, no content yet)
        self._build_primary_block(content_frame)
        
        # Step 4: Build secondary container (structure only, no content yet)
        self._build_secondary_block(content_frame)
        
        # Step 5: Build utility strip (always present at bottom)
        self._build_utility_strip(inspector_frame)
        
        # Step 6: NOW that all containers exist, show initial context
        self._show_campaign_context()
    
    def _build_context_header(self, parent: ttk.Frame) -> None:
        """Build context header: Single line, muted, no buttons."""
        header_frame = ttk.Frame(parent, style="Panel.TFrame", height=24)
        header_frame.pack(fill=tk.X, side=tk.TOP, padx=8, pady=(4, 0))
        header_frame.pack_propagate(False)
        
        self.context_label = ttk.Label(
            header_frame,
            text="CAMPAIGN",
            style="Context.TLabel"
        )
        self.context_label.pack(side=tk.LEFT, anchor="w")
    
    def _build_primary_block(self, parent: ttk.Frame) -> None:
        """Build primary block container (structure only, content added later)."""
        primary_frame = ttk.Frame(parent, style="Raised.TFrame")
        primary_frame.pack(fill=tk.BOTH, expand=False, pady=(8, 4))
        
        # Container for primary content
        self.primary_container = ttk.Frame(primary_frame, style="Raised.TFrame")
        self.primary_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        
        # Note: Content will be added by _show_campaign_context() or _show_character_context()
    
    def _build_secondary_block(self, parent: ttk.Frame) -> None:
        """Build secondary block container (structure only, content added later)."""
        secondary_frame = ttk.Frame(parent, style="Panel.TFrame")
        secondary_frame.pack(fill=tk.BOTH, expand=False, pady=(4, 4))
        
        self.secondary_container = ttk.Frame(secondary_frame, style="Panel.TFrame")
        self.secondary_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        
        # Note: Content will be added by context-specific methods
    
    def _build_utility_strip(self, parent: ttk.Frame) -> None:
        """Build utility strip: Debug button at bottom."""
        utility_frame = ttk.Frame(parent, style="Panel.TFrame", height=32)
        utility_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=8)
        utility_frame.pack_propagate(False)
        
        # Social Director (Debug) button
        debug_btn = ttk.Button(
            utility_frame,
            text="Social Director (Debug)",
            style="Debug.TButton",
            command=self._open_social_director
        )
        debug_btn.pack(side=tk.LEFT)
    
    def _build_bottom_feed(self, parent: ttk.Frame) -> None:
        """Build bottom system feed: Read-only log (15-20% height, min 100px)."""
        feed_frame = ttk.Frame(parent, style="Panel.TFrame", height=120)
        feed_frame.pack(fill=tk.BOTH, side=tk.BOTTOM)
        
        # Label
        feed_label = ttk.Label(
            feed_frame,
            text="System Feed",
            style="Secondary.TLabel",
            padding=(8, 4)
        )
        feed_label.pack(fill=tk.X, side=tk.TOP)
        
        # Text widget for feed
        self.feed_text = tk.Text(
            feed_frame,
            wrap="word",
            height=6,
            bg=THEME["bg_panel"],
            fg=THEME["fg_secondary"],
            font=("TkDefaultFont", 9),
            state=tk.DISABLED
        )
        self.feed_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=8, pady=(0, 8))
        
        feed_scrollbar = ttk.Scrollbar(
            feed_frame,
            orient=tk.VERTICAL,
            command=self.feed_text.yview
        )
        feed_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 8), padx=(0, 8))
        self.feed_text.configure(yscrollcommand=feed_scrollbar.set)

    # --- Inspector Context Helpers -------------------------------------------
    
    def _show_campaign_context(self) -> None:
        """Display campaign-level context in primary block."""
        self._clear_primary_block()
        self.context_label.config(text="CAMPAIGN")
        
        # Campaign info
        info_frame = ttk.Frame(self.primary_container, style="Raised.TFrame")
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        day_label = ttk.Label(
            info_frame,
            text=f"Campaign Day: {self.current_day}",
            style="Primary.TLabel",
            font=("TkDefaultFont", 10)
        )
        day_label.pack(anchor="w", pady=2)
        
        date_str = self.current_date.strftime("%Y-%m-%d")
        date_label = ttk.Label(
            info_frame,
            text=f"Date: {date_str}",
            style="Primary.TLabel",
            font=("TkDefaultFont", 10)
        )
        date_label.pack(anchor="w", pady=2)
        
        char_count = len(self.characters)
        chars_label = ttk.Label(
            info_frame,
            text=f"Characters Loaded: {char_count}",
            style="Primary.TLabel",
            font=("TkDefaultFont", 10)
        )
        chars_label.pack(anchor="w", pady=2)
        
        # Clear secondary block
        self._clear_secondary_block()
    
    def _show_character_context(self, char: Character) -> None:
        """Display character context in primary block."""
        self._clear_primary_block()
        self.context_label.config(text=f"CHARACTER · {char.name}")
        
        # Create content frame
        content_frame = ttk.Frame(self.primary_container, style="Raised.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=False)
        
        # Portrait (max 96×96px) on left
        portrait_frame = ttk.Frame(content_frame, style="Raised.TFrame")
        portrait_frame.pack(side=tk.LEFT, padx=(0, 12), pady=4)
        
        self.inspector_portrait_label = ttk.Label(
            portrait_frame,
            text="",
            background=THEME["bg_raised"]
        )
        self.inspector_portrait_label.pack()
        
        # Keep reference to prevent GC
        self.inspector_portrait_image = None
        self._update_inspector_portrait(char)
        
        # Info on right
        info_frame = ttk.Frame(content_frame, style="Raised.TFrame")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=4)
        
        # Name
        name_label = ttk.Label(
            info_frame,
            text=char.name,
            style="Primary.TLabel",
            font=("TkDefaultFont", 11, "bold")
        )
        name_label.pack(anchor="w")
        
        # Rank
        rank_display = char.rank_name or char.rank or "—"
        rank_label = ttk.Label(
            info_frame,
            text=f"Rank: {rank_display}",
            style="Secondary.TLabel",
            font=("TkDefaultFont", 9)
        )
        rank_label.pack(anchor="w")
        
        # Unit
        unit_text = char.unit.unit_name if char.unit else "No assignment"
        unit_label = ttk.Label(
            info_frame,
            text=f"Unit: {unit_text}",
            style="Secondary.TLabel",
            font=("TkDefaultFont", 9)
        )
        unit_label.pack(anchor="w")
        
        # Details button
        details_btn = ttk.Button(
            info_frame,
            text="Details…",
            style="Primary.TButton",
            command=lambda: self._open_character_detail(char)
        )
        details_btn.pack(anchor="w", pady=(8, 0))
        
        # Update secondary block with supplementary info
        self._show_character_secondary_info(char)
    
    def _show_character_secondary_info(self, char: Character) -> None:
        """Display supplementary character info in secondary block."""
        self._clear_secondary_block()
        
        # Profession
        prof_text = char.profession or "—"
        if char.secondary_profession:
            prof_text += f" / {char.secondary_profession}"
        
        prof_label = ttk.Label(
            self.secondary_container,
            text=f"Profession: {prof_text}",
            style="Secondary.TLabel",
            font=("TkDefaultFont", 9)
        )
        prof_label.pack(anchor="w", pady=2)
        
        # Age
        age_label = ttk.Label(
            self.secondary_container,
            text=f"Age: {char.age} ({char.age_group})",
            style="Secondary.TLabel",
            font=("TkDefaultFont", 9)
        )
        age_label.pack(anchor="w", pady=2)
        
        # Interaction points
        points_label = ttk.Label(
            self.secondary_container,
            text=f"Interaction Points: {char.daily_interaction_points}",
            style="Secondary.TLabel",
            font=("TkDefaultFont", 9)
        )
        points_label.pack(anchor="w", pady=2)
    
    def _clear_primary_block(self) -> None:
        """Clear all widgets from primary container."""
        for widget in self.primary_container.winfo_children():
            widget.destroy()
    
    def _clear_secondary_block(self) -> None:
        """Clear all widgets from secondary container."""
        for widget in self.secondary_container.winfo_children():
            widget.destroy()
    
    def _update_inspector_portrait(self, char: Character) -> None:
        """Load and display portrait in inspector (max 96×96px)."""
        if not PIL_AVAILABLE:
            self.inspector_portrait_label.config(text="No PIL")
            return
        
        portrait_path = PortraitHelper.resolve_portrait_path(char, prefer_casual=False)
        
        if portrait_path is None:
            self.inspector_portrait_label.config(text="No portrait")
            self.inspector_portrait_image = None
            return
        
        photo_image = PortraitHelper.load_portrait_image(portrait_path, (96, 96))
        if photo_image:
            self.inspector_portrait_image = photo_image
            self.inspector_portrait_label.config(image=self.inspector_portrait_image, text="")
        else:
            self.inspector_portrait_label.config(text="Error")
            self.inspector_portrait_image = None
    
    def _open_character_detail(self, char: Character) -> None:
        """Open character detail dialog."""
        CharacterDetailDialog(self.master, char, self.current_date, self.characters)
    
    def _open_social_director(self) -> None:
        """Open Social Director debug tool."""
        from social_director import SocialDirectorWindow
        
        try:
            # Create Social Director window with event manager
            SocialDirectorWindow(self.master, self.event_manager)
        except Exception as e:
            messagebox.showerror(
                "Error Opening Social Director",
                f"Failed to open Social Director:\n{e}"
            )
            traceback.print_exc()

    # --- Helper methods ---------------------------------------------------

    def _update_date_display(self):
        text = self.current_date.strftime("%A, %d.%m.%Y")
        self.date_label.config(text=text)

    def _on_date_left_click(self, event):
        if DatePickerDialog is None:
            return
        picker = DatePickerDialog(self.master, self.current_date)
        self.master.wait_window(picker.window)
        if getattr(picker, "result", None):
            self.current_date = picker.result
            self._update_date_display()
            self._update_day_events_bar()
            self._update_day_events_description()
            # Recalculate ages whenever the GUI date changes
            self._update_character_ages()
            # Update details of selected character so displayed age is refreshed
            if self.selected_character_id and self.selected_character_id in self.characters:
                self._update_details(self.characters[self.selected_character_id])

    def _on_date_right_click(self, event):
        if DetailedCalendarWindow is None:
            return
        DetailedCalendarWindow(self.master, self.event_manager, self.current_date)
    
    def _open_calendar(self):
        """Open the calendar window."""
        if DetailedCalendarWindow is None:
            return
        DetailedCalendarWindow(self.master, self.event_manager, self.current_date)

    def _update_day_events_bar(self):
        """Update system feed with day events (removed - events now in feed only)."""
        pass

    def _update_day_events_description(self):
        """Update system feed with event descriptions (removed - events now in feed only)."""
        pass

    def _describe_event(self, event):
        """Generate event description text."""
        t = event.title.lower()
        if "simulator" in t or "übung" in t:
            return "The unit performs simulator training focusing on tactics and coordination."
        if "wartung" in t or "maintenance" in t:
            return "The mechs undergo scheduled maintenance and repairs."
        return ""

    def _ensure_log_window(self):
        if self.log_window and self.log_window.winfo_exists():
            return
        self.log_window = tk.Toplevel(self.master)
        self.log_window.title("Log")
        self.log_window.geometry("700x400")

        frame = ttk.Frame(self.log_window)
        frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(frame, wrap="word")
        self.log_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        def on_close():
            self.log_window.destroy()
            self.log_window = None
            self.log_text = None

        self.log_window.protocol("WM_DELETE_WINDOW", on_close)

    def _show_log_window(self):
        self._ensure_log_window()
        if self.log_window:
            self.log_window.deiconify()
            self.log_window.lift()

    def _log(self, text: str) -> None:
        # Use popup log window
        self._ensure_log_window()
        if self.log_text:
            self.log_text.insert("end", text + "\n")
            self.log_text.see("end")

    def _clear_tree(self) -> None:
        self.tree.delete(*self.tree.get_children(self.root_node))
        self.no_toe_node = self.tree.insert(self.root_node, "end", text="Ohne TO&E", open=True)

    def _populate_tree(self) -> None:
        self._clear_tree()

        # First group by force and unit
        forces: Dict[str, Dict[str, List[Character]]] = {}
        no_toe: List[Character] = []

        for char in self.characters.values():
            if char.unit is None:
                no_toe.append(char)
            else:
                forces.setdefault(char.unit.force_name, {})
                forces[char.unit.force_name].setdefault(char.unit.unit_name, [])
                forces[char.unit.force_name][char.unit.unit_name].append(char)

        for force_name, units in sorted(forces.items()):
            force_node = self.tree.insert(self.root_node, "end", text=force_name, open=True)
            for unit_name, chars in sorted(units.items()):
                unit_node = self.tree.insert(force_node, "end", text=unit_name, open=True)
                for c in sorted(chars, key=lambda x: x.name):
                    self.tree.insert(unit_node, "end", iid=c.id, text=c.label())

        for c in sorted(no_toe, key=lambda x: x.name):
            self.tree.insert(self.no_toe_node, "end", iid=c.id, text=c.label())

        self.tree.item(self.root_node, open=True)
        self.tree.item(self.no_toe_node, open=True)

    def _log_to_feed(self, text: str) -> None:
        """Log message to the bottom system feed."""
        self.feed_text.config(state=tk.NORMAL)
        self.feed_text.insert("end", text + "\n")
        self.feed_text.see("end")
        self.feed_text.config(state=tk.DISABLED)

    def _add_event(self, text: str) -> None:
        """Add event text to system feed."""
        self._log_to_feed(text)

    def _clear_events(self) -> None:
        """Clear events (no-op, events are in feed now)."""
        pass

    # ----------------- OLD portrait handling (no longer needed) -----------------

    def _update_details(self, char: Optional[Character]) -> None:
        """Update inspector panel with character or campaign context."""
        if char is None:
            # Show campaign context
            self._show_campaign_context()
            return
        
        # Show character context in inspector
        self._show_character_context(char)

    # ----------------- Age calculation helpers -----------------
    def _calculate_age(self, birth_date: date, reference_date: date) -> int:
        """Calculate full years between birth_date and reference_date."""
        if birth_date is None:
            return 0
        age = reference_date.year - birth_date.year
        try:
            # If birthday hasn't happened yet this year, subtract one
            if reference_date < birth_date.replace(year=reference_date.year):
                age -= 1
        except ValueError:
            # handle Feb 29 on non-leap year by comparing month/day manually
            if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
                age -= 1
        return age

    def _update_character_ages(self) -> None:
        """Recalculate ages for all loaded characters using the current GUI date."""
        if not getattr(self, "characters", None):
            return
        for char in self.characters.values():
            bdate = getattr(char, "birthday", None)
            if bdate:
                char.age = self._calculate_age(bdate, self.current_date)

    # --- Event handlers (selection/partners/import/rolls) -----------------

    def _on_tree_select(self, event: object) -> None:
        sel = self.tree.selection()
        if not sel:
            self.selected_character_id = None
            self._update_details(None)
            return

        cid = sel[0]
        char = self.characters.get(cid)
        if char is None:
            self.selected_character_id = None
            self._update_details(None)
            return

        self.selected_character_id = cid
        self._update_details(char)

    def _on_tree_right_click(self, event: object) -> None:
        """Handle right-click on tree view to open character detail window."""
        # Identify the item at the click position
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # Check if this is a character node (not a force/unit grouping)
        char = self.characters.get(item_id)
        if char is None:
            # This is a grouping node, ignore
            return

        # Select the item
        self.tree.selection_set(item_id)
        self.selected_character_id = item_id
        self._update_details(char)

        # Open the character detail dialog with character lookup for resolving relationship names
        CharacterDetailDialog(self.master, char, self.current_date, self.characters)

    def _export_campaign_data(self) -> None:
        """Export campaign data (personnel, TO&E, metadata) from a .cpnx file."""
        # Select .cpnx file
        cpnx_path = filedialog.askopenfilename(
            title="Select MekHQ Campaign File (.cpnx)",
            filetypes=[
                ("MekHQ Campaigns", "*.cpnx *.cpnx.gz"),
                ("All Files", "*.*")
            ],
        )
        if not cpnx_path:
            return
        
        try:
            # Use the canonical export directory
            export_dir = EXPORT_DIR
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # Load the campaign file
            self._log(f"Loading campaign file: {Path(cpnx_path).name}")
            root = mekhq_personnel_exporter.load_cpnx(cpnx_path)
            
            # Extract data
            self._log("Extracting personnel data...")
            personnel_data = mekhq_personnel_exporter.parse_personnel(root)
            
            self._log("Extracting TO&E data...")
            forces_data = mekhq_personnel_exporter.parse_forces(root)
            units_data = mekhq_personnel_exporter.parse_units(root)
            
            self._log("Extracting campaign metadata...")
            campaign_metadata = mekhq_personnel_exporter.parse_campaign_metadata(root)
            
            # Export to JSON files
            self._log("Exporting to JSON files...")
            personnel_path = export_dir / "personnel_complete.json"
            toe_path = export_dir / "toe_complete.json"
            meta_path = export_dir / "campaign_meta.json"
            
            mekhq_personnel_exporter.export_personnel_to_json(personnel_data, str(personnel_path))
            mekhq_personnel_exporter.export_toe_to_json(forces_data, units_data, str(toe_path))
            mekhq_personnel_exporter.export_campaign_meta_to_json(campaign_metadata, str(meta_path))
            
            # Count total forces including sub-forces
            total_forces = mekhq_personnel_exporter.count_forces_recursive(forces_data)
            
            # Log success
            self._log(f"✅ Export complete:")
            self._log(f"  - {len(personnel_data)} personnel")
            self._log(f"  - {len(forces_data)} root forces, {total_forces} total (with sub-forces)")
            self._log(f"  - {len(units_data)} units")
            self._log(f"  - Campaign date: {campaign_metadata.get('campaign_date', 'N/A')}")
            self._log(f"  - Rank system: {campaign_metadata.get('rank_system', 'N/A')}")
            
            messagebox.showinfo(
                "Export Successful",
                f"Campaign data exported successfully!\n\n"
                f"Files saved to:\n{export_dir}\n\n"
                f"Personnel: {len(personnel_data)} characters\n"
                f"Root Forces: {len(forces_data)}\n"
                f"Total Forces (incl. sub-forces): {total_forces}\n"
                f"Units: {len(units_data)}\n"
                f"Date: {campaign_metadata.get('campaign_date', 'N/A')}\n"
                f"Rank System: {campaign_metadata.get('rank_system', 'N/A')}"
            )
            
        except Exception as exc:
            self._log(f"❌ Export failed: {exc}")
            messagebox.showerror("Export Failed", str(exc))
            traceback.print_exc()

    def _import_campaign_meta(self) -> None:
        """Import campaign metadata (date and rank system) from a .cpnx file."""
        path = filedialog.askopenfilename(
            title="Select MekHQ Campaign File (.cpnx)",
            filetypes=[
                ("MekHQ Campaigns", "*.cpnx *.cpnx.gz"),
                ("All Files", "*.*")
            ],
        )
        if not path:
            return

        try:
            # Use the exporter to parse the .cpnx file
            root = mekhq_personnel_exporter.load_cpnx(path)
            metadata = mekhq_personnel_exporter.parse_campaign_metadata(root)
            
            campaign_date_str = metadata.get("campaign_date")
            rank_system = metadata.get("rank_system")
            
            # Update GUI date if campaign date is available
            if campaign_date_str:
                try:
                    # Parse YYYY-MM-DD format
                    self.current_date = datetime.strptime(campaign_date_str, "%Y-%m-%d").date()
                    self._update_date_display()
                    self._log(f"Campaign date set to: {campaign_date_str}")
                except Exception as e:
                    self._log(f"Warning: Could not parse campaign date '{campaign_date_str}': {e}")
            
            # Set rank system in the rank resolver
            if rank_system:
                rank_resolver = get_rank_resolver()
                rank_resolver.set_rank_system(rank_system)
                self._log(f"Rank system set to: {rank_system}")
                
                # If characters are already loaded, re-resolve their rank names
                if self.characters:
                    for char in self.characters.values():
                        if char.rank is not None:
                            try:
                                rank_id = int(char.rank)
                                char.rank_name = rank_resolver.resolve_rank_name(rank_id)
                            except (ValueError, TypeError):
                                char.rank_name = f"Rank {char.rank}"
                    
                    # Refresh display if a character is selected
                    if self.selected_character_id and self.selected_character_id in self.characters:
                        self._update_details(self.characters[self.selected_character_id])
            
            # Show success message
            msg_parts = []
            if campaign_date_str:
                msg_parts.append(f"Date: {campaign_date_str}")
            if rank_system:
                msg_parts.append(f"Rank System: {rank_system}")
            
            if msg_parts:
                messagebox.showinfo(
                    "Campaign Metadata Loaded",
                    "Successfully loaded:\n" + "\n".join(msg_parts)
                )
            else:
                messagebox.showwarning(
                    "No Metadata Found",
                    "No campaign date or rank system found in the file."
                )
                
        except Exception as exc:
            messagebox.showerror("Error Loading Campaign Metadata", str(exc))
            traceback.print_exc()

    def _import_personnel(self) -> None:
        path = filedialog.askopenfilename(
            title="WÃ¤hle personnel_complete.json",
            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return

        try:
            self.characters = load_campaign(path)
            reset_daily_pools(self.characters)
            # Recalculate ages relative to the current GUI date
            self._update_character_ages()
            self._populate_tree()
            self._log(f"Personal aus {Path(path).name} geladen ({len(self.characters)} Charaktere).")
            messagebox.showinfo("Erfolg", f"{len(self.characters)} Charaktere geladen!")
            # Update details and day/event displays (if any)
            self._update_day_events_bar()
            self._update_day_events_description()
        except Exception as exc:
            messagebox.showerror("Fehler beim Laden", str(exc))
            traceback.print_exc()

    def _import_toe(self) -> None:
        if not self.characters:
            messagebox.showinfo("Hinweis", "Bitte zuerst Personal importieren.")
            return

        path = filedialog.askopenfilename(
            title="WÃ¤hle toe_complete.json",
            filetypes=[("JSON", "*.json"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return

        try:
            apply_toe_structure(path, self.characters)
            self._populate_tree()
            self._log(f"TO&E aus {Path(path).name} geladen und angewendet.")
            messagebox.showinfo("Erfolg", "TO&E-Struktur angewendet!")
        except Exception as exc:
            messagebox.showerror("Fehler beim Laden der TO&E", str(exc))
            traceback.print_exc()

    def _set_external_portrait_folder(self) -> None:
        """Open dialog to set external portrait folder."""
        folder = filedialog.askdirectory(
            title="Select External Portrait Folder",
            mustexist=True
        )
        if not folder:
            return
        
        # Save to config
        portrait_config.save_config(Path(folder))
        
        messagebox.showinfo(
            "External Portrait Folder Set",
            f"External portrait folder set to:\n{folder}\n\nPortraits will now be searched in both the module folder and this external folder."
        )
        
        # Refresh current character display if any
        if self.selected_character_id and self.selected_character_id in self.characters:
            self._update_details(self.characters[self.selected_character_id])

    def _next_day(self) -> None:
        if not self.characters:
            messagebox.showinfo("Notice", "No characters loaded.")
            return

        # campaign day counter remains
        self.current_day += 1

        # advance the real date, update displays
        self.current_date += timedelta(days=1)
        self._update_date_display()
        
        # Update calendar widget date if it exists
        if hasattr(self, 'calendar_widget'):
            self.calendar_widget.current_date = self.current_date
            self.calendar_widget._update_display()

        # Update ages when the day advances
        self._update_character_ages()

        reset_daily_pools(self.characters)
        self._log_to_feed(f"--- Day {self.current_day} ---")
        self._log_to_feed(f"Interaction points reset.")

        # Execute scheduled events for this date
        if self.event_manager:
            events = self.event_manager.get_events_for_date(self.current_date)
            if events:
                self._log_to_feed(f"Executing {len(events)} scheduled event(s)...")
                logs = self.event_manager.execute_events_for_date(self.current_date, self.characters)
                for log in logs:
                    self._log_to_feed(f"  • {log.event_name} (ID:{log.event_id})")

        # Update details of the currently selected character
        if self.selected_character_id and self.selected_character_id in self.characters:
            self._update_details(self.characters[self.selected_character_id])


def main() -> None:
    root = tk.Tk()
    # Initialize dark military theme before building UI
    init_dark_military_style(root)
    app = MekSocialGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
