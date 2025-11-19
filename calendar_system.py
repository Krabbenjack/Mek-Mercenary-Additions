class CalendarSystem:
    def __init__(self):
        self.events = []

    def add_event(self, event):
        self.events.append(event)

    def get_events(self):
        return self.events

    def clear_events(self):
        self.events.clear()