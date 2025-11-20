441
442
443
444
445
446
447
448
449
450
451
452
453
454
455
456
457
458
459
460
461
462
463
464
465
466
467
468
469
470
471
472
473
474
475
476
477
478
479
480
481
482
483
484
485
486
487
488
489
490
491
492
493
494
495
496
497
498
499
500
501
502
503
504
505
506
507
508
509
510
511
"""
        self.date_label.pack(pady=6)

        instruction_text = ("Left-click: Open date picker\nRight-click: Open detailed calendar view")
        instruction = tk.Label(self.root, text=instruction_text, font=("Arial", 10), fg="gray", justify=tk.CENTER)
        instruction.pack(pady=8)

        self._update_date_display()

    def _bind_mouse_events(self):
        # Left-click is <Button-1>, right-click is <Button-3>
        self.date_frame.bind("<Button-1>", self._on_date_left_click)
        self.date_frame.bind("<Button-3>", self._on_date_right_click)
        self.weekday_label.bind("<Button-1>", self._on_date_left_click)
        self.weekday_label.bind("<Button-3>", self._on_date_right_click)
        self.date_label.bind("<Button-1>", self._on_date_left_click)
        self.date_label.bind("<Button-3>", self._on_date_right_click)

    def _update_date_display(self):
        weekday_name = self.current_date.strftime("%A")
        formatted_date = self.current_date.strftime("%d.%m.%Y")
        self.weekday_label.config(text=weekday_name)
        self.date_label.config(text=formatted_date)

    def _on_date_left_click(self, event):
        # Open date picker dialog; on confirm update main date display
        picker = DatePickerDialog(self.root, self.current_date)
        self.root.wait_window(picker.window)
        if picker.result:
            self.current_date = picker.result
            self._update_date_display()

    def _on_date_right_click(self, event):
        # Open detailed calendar window showing current_date's month
        DetailedCalendarWindow(self.root, self.event_manager, self.current_date)


# ============================================================================
# MAIN ENTRY POINT & CUSTOMIZATION GUIDE
# ============================================================================

def main():
    """
    Main entry point for the calendar application.

    Look & feel:
    - Change color and font values in widget creation (bg=, fg=, font=(...))
    Persistence:
    - Implement EventManager.save_events/load_events with JSON/SQLite/CSV
    Embedding:
    - Import EventManager or MainCalendarWindow into other modules and integrate into your app's Tk root.
    """
    root = tk.Tk()
    app = MainCalendarWindow(root)

    # sample events for demonstration
    today = datetime.now().date()
    app.event_manager.add_event("Team Meeting", today, RecurrenceType.WEEKLY)
    app.event_manager.add_event("Dentist Appointment", today + timedelta(days=5), RecurrenceType.ONCE)
    # birthday example (replace year if necessary)
    try:
        birthday = today.replace(month=12, day=25)
    except ValueError:
        birthday = today
    app.event_manager.add_event("Birthday Reminder", birthday, RecurrenceType.YEARLY)

    root.mainloop()


if __name__ == "__main__":
    main()

Use Control + Shift + m to toggle the tab
