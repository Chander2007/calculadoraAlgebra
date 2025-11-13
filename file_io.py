import os
import json


def save_file_path(base_dir=None):
    base = base_dir if base_dir else os.path.dirname(__file__)
    return os.path.join(base, "matrices_guardadas.json")


def read_saved_json(path=None):
    p = path if path else save_file_path()
    if not os.path.exists(p):
        return {}
    try:
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_saved_json(data, path=None):
    p = path if path else save_file_path()
    try:
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False


def collect_entries_as_strings(entries):
    rows = len(entries)
    cols = len(entries[0]) if rows else 0
    out = []
    for i in range(rows):
        row = []
        for j in range(cols):
            val = entries[i][j].get().strip()
            row.append(val if val != "" else "0")
        out.append(row)
    return out


def fill_entries_from_strings(entries, data_2d):
    rows = len(entries)
    cols = len(entries[0]) if rows else 0
    if rows != len(data_2d) or (rows and cols != len(data_2d[0])):
        return False
    for i in range(rows):
        for j in range(cols):
            entries[i][j].delete(0, 'end')
            entries[i][j].insert(0, str(data_2d[i][j]))
    return True
