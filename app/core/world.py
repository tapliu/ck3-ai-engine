import os
import random
from collections import defaultdict
from app.models.character import Character


def _load_excel():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "xczyw_xs.xlsx")
    if not os.path.isfile(path):
        return []

    try:
        import openpyxl
    except ImportError:
        return []

    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb["Sheet5"]
    rows = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[2] is None:
            continue
        rows.append((row[1], row[2], row[3], row[4], row[5], row[6], row[7] or ""))
    wb.close()
    return rows


DATA = _load_excel()


class World:
    def __init__(self):
        self.characters = {}
        self.rel = defaultdict(dict)
        self.next_id = 0

        for d in DATA:
            self.create(*d)

    def create(self, gender, name, l, w, i, p, desc=""):
        c = Character(self.next_id, name, gender, l, w, i, p, desc)
        self.characters[self.next_id] = c

        for k in self.characters:
            if k != self.next_id:
                v = random.randint(-30, 30)
                self.rel[k][self.next_id] = v
                self.rel[self.next_id][k] = v

        self.next_id += 1

    def alive(self):
        return [c for c in self.characters.values() if c.alive]

    def get(self, name):
        for c in self.characters.values():
            if c.name == name:
                return c

    def export(self):
        return {
            "round": getattr(self, "engine", None) and self.engine.round or 0,
            "characters":[c.to_dict() for c in self.alive()]
        }


world = World()
