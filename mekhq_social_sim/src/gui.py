from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, Optional, List
from datetime import date, timedelta, datetime

# Ensure src is on sys.path so the merk_calendar package is importable.
repo_root = Path(__file__).resolve().parents[2]  # mekhq_social_sim/src/gui.py -> repo root
src_path = repo_root.joinpath("src")
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Calendar system imports (required by the full integration)
try:
    from merk_calendar.calendar_system import (
        EventManager,
        RecurrenceType,
        DetailedCalendarWindow,
        DatePickerDialog,
    )
except Exception:
    # If calendar package is missing the GUI still runs, calendar features are disabled.
    EventManager = None
    RecurrenceType = None
    DetailedCalendarWindow = None
    DatePickerDialog = None

from models import Character
from data_loading import load_campaign, apply_toe_structure
from interaction_pool import reset_daily_pools, has_points
from roll_engine import perform_random_interaction, perform_manual_interaction
from social_modifiers import combined_social_modifier

def reset_daily_pools(characters: Dict[str, Character]) -> None:
    """Reset daily interaction pools (simple example implementation)."""
    for c in characters.values():
        c.daily_interaction_points = 0


class MekSocialGUI:
    def __init__(self, master: tk.Tk) -> None:
        self.master = master
        self.master.title("MekHQ Social Simulator")
        self.master.geometry("1200x800")

        self.characters: Dict[str, Character] = {}
        self.current_day: int = 1
        self.selected_character_id: Optional[str] = None
        self.selected_partner_index: Optional[int] = None

        # Real-world date and event manager
        self.current_date: date = date.today()
        self.event_manager = EventManager() if EventManager is not None else None

        # Log popup state
        self.log_window = None
        self.log_text = None

        self._build_widgets()

    # --- GUI construction -------------------------------------------------

    def _build_widgets(self) -> None:
        # Notebook für Tabs
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Hauptansicht
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Hauptansicht")

        # Tab 2: Ereignisse
        self.events_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.events_tab, text="Ereignisse")

        self._build_main_tab()
        self._build_events_tab()

    def _build_main_tab(self) -> None:
        main_pane = ttk.PanedWindow(self.main_tab, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left: tree
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)

        self.tree = ttk.Treeview(left_frame, columns=("type",), show="tree")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.root_node = self.tree.insert("", "end", text="Personal", open=True)
        self.no_toe_node = self.tree.insert(self.root_node, "end", text="Ohne TO&E", open=True)

        # Right: info + controls
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=2)

        top_bar = ttk.Frame(right_frame)
        top_bar.pack(fill=tk.X, pady=4)

        # Replace day label with real date label
        self.date_label = ttk.Label(top_bar, text="", padding=4, relief="groove")
        self.date_label.pack(side=tk.LEFT, padx=4)
        self.date_label.bind("<Button-1>", self._on_date_left_click)
        self.date_label.bind("<Button-3>", self._on_date_right_click)
        self._update_date_display()

        next_day_btn = ttk.Button(top_bar, text="Nächster Tag", command=self._next_day)
        next_day_btn.pack(side=tk.LEFT, padx=4)

        import_pers_btn = ttk.Button(
            top_bar, text="Importiere Personal (JSON)", command=self._import_personnel
        )
        import_pers_btn.pack(side=tk.LEFT, padx=4)

        import_toe_btn = ttk.Button(
            top_bar, text="Importiere TO&E (JSON)", command=self._import_toe
        )
        import_toe_btn.pack(side=tk.LEFT, padx=4)

        # Day events summary bar (under date label)
        self.day_events_frame = ttk.Frame(right_frame)
        self.day_events_frame.pack(fill=tk.X, padx=4, pady=(0, 4))

        self.day_events_label = ttk.Label(self.day_events_frame, text="No events for this day.")
        self.day_events_label.pack(side=tk.LEFT)

        # Character details
        details_frame = ttk.LabelFrame(right_frame, text="Charakter")
        details_frame.pack(fill=tk.X, padx=4, pady=4)

        self.details_text = tk.Text(details_frame, height=8, wrap="word")
        self.details_text.pack(fill=tk.X)

        # Potential partners & manual roll
        partners_frame = ttk.LabelFrame(right_frame, text="Mögliche Partner")
        partners_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        partner_inner = ttk.Frame(partners_frame)
        partner_inner.pack(fill=tk.BOTH, expand=True)

        self.partner_list = tk.Listbox(partner_inner, height=8)
        self.partner_list.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.partner_list.bind("<<ListboxSelect>>", self._on_partner_select)

        partner_scroll = ttk.Scrollbar(partner_inner, orient=tk.VERTICAL, command=self.partner_list.yview)
        partner_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.partner_list.configure(yscrollcommand=partner_scroll.set)

        # Buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X, padx=4, pady=4)

        self.manual_roll_btn = ttk.Button(
            button_frame,
            text="Manueller Wurf mit ausgewähltem Partner",
            command=self._trigger_manual_roll,
            state=tk.DISABLED
        )
        self.manual_roll_btn.pack(side=tk.LEFT, padx=2)

        random_roll_btn = ttk.Button(
            button_frame,
            text="Zufälliger Partner-Wurf",
            command=self._trigger_random_roll
        )
        random_roll_btn.pack(side=tk.LEFT, padx=2)

        # Show Log button (log moved to popup)
        show_log_btn = ttk.Button(button_frame, text="Show Log", command=self._show_log_window)
        show_log_btn.pack(side=tk.RIGHT, padx=2)

        # Detailed event description area (replaces inline log)
        events_frame = ttk.LabelFrame(right_frame, text="Events on current day")
        events_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.day_events_text = tk.Text(events_frame, wrap="word")
        self.day_events_text.pack(fill=tk.BOTH, expand=True)

        # Initialize event/UI views
        self._update_day_events_bar()
        self._update_day_events_description()

    def _build_events_tab(self) -> None:
        # Frame für Ereignisse
        events_frame = ttk.Frame(self.events_tab)
        events_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Label
        label = ttk.Label(events_frame, text="Ereignisse & Fluff-Text", font=("Arial", 14, "bold"))
        label.pack(pady=5)

        # Text-Widget für Ereignisse
        text_frame = ttk.Frame(events_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.events_text = tk.Text(text_frame, wrap="word", font=("Arial", 10))
        self.events_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        events_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.events_text.yview)
        events_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_text.configure(yscrollcommand=events_scroll.set)

        # Button zum Löschen
        clear_btn = ttk.Button(events_frame, text="Ereignisse löschen", command=self._clear_events)
        clear_btn.pack(pady=5)

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

    def _update_day_events_bar(self):
        if self.event_manager is None:
            self.day_events_label.config(text="Events disabled")
            return
        events = self.event_manager.get_events_for_date(self.current_date)
        if not events:
            text = "No events for this day."
        else:
            titles = ", ".join(e.title for e in events)
            text = f"Events today: {titles}"
        self.day_events_label.config(text=text)

    def _update_day_events_description(self):
        if self.event_manager is None:
            self.day_events_text.delete("1.0", "end")
            self.day_events_text.insert("end", "Events disabled")
            return

        self.day_events_text.delete("1.0", "end")
        events = self.event_manager.get_events_for_date(self.current_date)

        if not events:
            self.day_events_text.insert("end", "No events for this day.")
            return

        for event in events:
            self.day_events_text.insert("end", f"- {event.title} ({event.recurrence_type.value})\n")
            desc = self._describe_event(event)
            if desc:
                self.day_events_text.insert("end", f"  {desc}\n\n")

    def _describe_event(self, event):
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

    def _log_simple(self, text: str) -> None:
        # Internal helper to append to the events tab text (keeps events tab behavior)
        self.events_text.insert("end", text + "\n\n")
        self.events_text.see("end")

    def _add_event(self, text: str) -> None:
        """Fügt einen Ereignis-Text zum Ereignis-Tab hinzu"""
        self._log_simple(text)

    def _clear_events(self) -> None:
        self.events_text.delete("1.0", tk.END)

    def _update_details(self, char: Optional[Character]) -> None:
        self.details_text.delete("1.0", "end")
        self.partner_list.delete(0, tk.END)
        self.selected_partner_index = None
        self.manual_roll_btn.config(state=tk.DISABLED)

        if char is None:
            return

        # make sure details show current birthday and recalculated age
        birthday_str = char.birthday.strftime("%Y-%m-%d") if char.birthday else "-"
        lines = [
            f"Name: {char.name}",
            f"Rufname: {char.callsign or '-'}",
            f"Alter: {char.age} ({char.age_group})",
            f"Geburtstag: {birthday_str}",
            f"Beruf: {char.profession or '-'}",
            f"Interaktionspunkte: {char.daily_interaction_points}",
        ]
        if char.unit:
            lines.append(
                f"Einheit: {char.unit.unit_name} / {char.unit.force_name} ({char.unit.force_type})"
            )
        else:
            lines.append("Einheit: (keine TO&E-Zuordnung)")

        if char.traits:
            lines.append("Traits:")
            for k, v in sorted(char.traits.items()):
                lines.append(f"  - {k}: {v}")

        if char.friendship:
            lines.append("Beziehungen:")
            for pid, fval in sorted(char.friendship.items(), key=lambda x: -x[1])[:10]:
                partner = self.characters.get(pid)
                if partner:
                    lines.append(f"  - {partner.label()}: {fval}")

        # Show potential partners (sorted by modifier)
        self.potential_partners = []
        partners_with_mods = []
        for other in self.characters.values():
            if other.id == char.id:
                continue
            mod, _ = combined_social_modifier(char, other)
            partners_with_mods.append((mod, other))

        partners_with_mods.sort(key=lambda x: -x[0])
        for mod, other in partners_with_mods[:30]:
            self.potential_partners.append(other)
            self.partner_list.insert(tk.END, f"{other.label()} ({mod:+d})")

        self.details_text.insert(tk.END, "\n".join(lines))

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

    def _on_partner_select(self, event: object) -> None:
        selection = self.partner_list.curselection()
        if not selection:
            self.selected_partner_index = None
            self.manual_roll_btn.config(state=tk.DISABLED)
            return

        self.selected_partner_index = selection[0]

        # Aktiviere Button nur wenn Charakter Punkte hat
        if self.selected_character_id:
            actor = self.characters.get(self.selected_character_id)
            if actor and has_points(actor):
                self.manual_roll_btn.config(state=tk.NORMAL)
            else:
                self.manual_roll_btn.config(state=tk.DISABLED)

    def _import_personnel(self) -> None:
        path = filedialog.askopenfilename(
            title="Wähle personnel_complete.json",
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
            import traceback
            traceback.print_exc()

    def _import_toe(self) -> None:
        if not self.characters:
            messagebox.showinfo("Hinweis", "Bitte zuerst Personal importieren.")
            return

        path = filedialog.askopenfilename(
            title="Wähle toe_complete.json",
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
            import traceback
            traceback.print_exc()

    def _next_day(self) -> None:
        if not self.characters:
            messagebox.showinfo("Hinweis", "Keine Charaktere geladen.")
            return

        # campaign day counter remains
        self.current_day += 1

        # advance the real date, update displays
        self.current_date += timedelta(days=1)
        self._update_date_display()
        self._update_day_events_bar()
        self._update_day_events_description()

        # Update ages when the day advances
        self._update_character_ages()

        reset_daily_pools(self.characters)
        self._log(f"--- Tag {self.current_day} ---")
        self._log(f"Interaktionspunkte zurückgesetzt.")

        # Update details of the currently selected character
        if self.selected_character_id and self.selected_character_id in self.characters:
            self._update_details(self.characters[self.selected_character_id])

    def _trigger_manual_roll(self) -> None:
        if not self.characters:
            messagebox.showinfo("Hinweis", "Keine Charaktere geladen.")
            return

        if not self.selected_character_id:
            messagebox.showinfo("Hinweis", "Bitte zuerst einen Charakter auswählen.")
            return

        if self.selected_partner_index is None:
            messagebox.showinfo("Hinweis", "Bitte einen Partner aus der Liste auswählen.")
            return

        actor = self.characters.get(self.selected_character_id)
        if actor is None:
            return

        if not has_points(actor):
            messagebox.showinfo(
                "Keine Punkte",
                f"{actor.label()} hat heute keine Interaktionspunkte mehr.",
            )
            return

        # Hole den ausgewählten Partner
        if self.selected_partner_index >= len(self.potential_partners):
            messagebox.showinfo("Fehler", "Ungültiger Partner-Index.")
            return

        partner = self.potential_partners[self.selected_partner_index]

        result = perform_manual_interaction(actor, partner)
        if result is None:
            messagebox.showinfo("Fehler", "Interaktion konnte nicht durchgeführt werden.")
            return

        # Log the interaction
        for line in result.log_lines:
            self._log(line)

        # Generate and display fluff text
        fluff = self._generate_fluff(result)
        self._add_event(fluff)

        # Refresh details
        self._update_details(actor)

    def _trigger_random_roll(self) -> None:
        if not self.characters:
            messagebox.showinfo("Hinweis", "Keine Charaktere geladen.")
            return

        if not self.selected_character_id:
            messagebox.showinfo("Hinweis", "Bitte zuerst einen Charakter im Baum auswählen.")
            return

        actor = self.characters.get(self.selected_character_id)
        if actor is None:
            return

        if not has_points(actor):
            messagebox.showinfo(
                "Keine Punkte",
                f"{actor.label()} hat heute keine Interaktionspunkte mehr.",
            )
            return

        result = perform_random_interaction(actor, self.characters.values())
        if result is None:
            messagebox.showinfo("Keine Partner", "Es konnten keine passenden Partner gefunden werden.")
            return

        for line in result.log_lines:
            self._log(line)

        # Generate and display fluff text
        fluff = self._generate_fluff(result)
        self._add_event(fluff)

        # Refresh details
        self._update_details(actor)

    def _generate_fluff(self, result) -> str:
        """Generiert einen Fluff-Text basierend auf dem Würfelergebnis"""
        actor_name = result.actor.callsign or result.actor.name
        partner_name = result.partner.callsign or result.partner.name

        fluff_lines = [
            f"=== Tag {self.current_day} ===",
            f"Begegnung: {actor_name} und {partner_name}",
            ""
        ]

        if result.success:
            # Positive Interaktion
            if result.roll >= 10:
                fluff_lines.append(
                    f"Ein außergewöhnlich gutes Gespräch entwickelt sich zwischen {actor_name} "
                    f"und {partner_name}. Die beiden finden gemeinsame Interessen und verstehen "
                    f"sich auf Anhieb prächtig."
                )
            else:
                fluff_lines.append(
                    f"{actor_name} und {partner_name} verbringen einige Zeit miteinander. "
                    f"Die Unterhaltung verläuft angenehm und beide fühlen sich danach "
                    f"ein wenig besser verbunden."
                )
        else:
            # Negative Interaktion
            if result.roll <= 4:
                fluff_lines.append(
                    f"Die Begegnung zwischen {actor_name} und {partner_name} verläuft katastrophal. "
                    f"Ein hitziger Streit bricht aus, und beide gehen mit einem schlechten "
                    f"Gefühl auseinander."
                )
            else:
                fluff_lines.append(
                    f"{actor_name} und {partner_name} geraten aneinander. Die Atmosphäre "
                    f"ist angespannt, und das Gespräch endet mit gegenseitiger Verstimmung."
                )

        fluff_lines.append("")
        fluff_lines.append(f"Würfelwurf: {result.roll} gegen Ziel {result.target}")
        fluff_lines.append(f"Beziehung: {result.new_friendship}")

        return "\n".join(fluff_lines)


def main() -> None:
    root = tk.Tk()
    app = MekSocialGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
