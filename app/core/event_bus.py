# app/core/event_bus.py

class EventBus:
    def __init__(self):
        self.events = []

    def emit(self, e):
        self.events.append(e)

    def pop(self):
        e = self.events[:]
        self.events = []
        return e
