# Contributing to DoALL

Erm ig yall might wanna contribute ? sure. We use uv instead of pip cuz its better so install it first.

## Quickstart

1. **Fork** the repo on GitHub
2. **Clone** your fork:

```bash
git clone git@github.com:<your-username>/DoALL.git
cd DoALL
```

3. **Create a branch** (see naming below):

```bash
git checkout -b feature/my-module
```

4. **Create a virtual environment**:

```bash
uv venv
source .venv/bin/activate
```

5. **Run** the app in development mode:

```bash
uv run textual run --dev main.py
```

6. **Run Debug** (Optional):
```bash
uv run textual console
```



## Branch naming

```
<category>/<module>
```

| Category | Use for |
|---|---|
| `feature/` | New modules or major features |
| `fix/` | Bug fixes |
| `refactor/` | Code cleanup, no behavior change |

Examples: `feature/habit-tracker`, `fix/budget-overflow`

---

## Adding a new module

A module is a tab in the app. Each one lives under `tabs/<name>/` with this structure.

You may also add more files to make it cleaner, just stick them in the same folder.

```
tabs/<name>/
├── <name>.py      # TabPane subclass + main Widget (optional)
├── <name>.tcss    # Styles
├── modals.py      # ModalScreen subclasses (optional)
└── db.py          # SQLite persistence (optional)
```


### Step-by-step

**1. Create the directory and files**

```bash
mkdir tabs/<name>
touch tabs/<name>/<name>.py
touch tabs/<name>/<name>.tcss
# optional:
touch tabs/<name>/modals.py
touch tabs/<name>/db.py
```

**2. Write the TabPane + Widget** (`tabs/<name>/<name>.py`)

See any module for reference. Or view the [Template](tabs/template).

Every module needs a `TabPane` wrapper and may have `Widget` (Optional but cleaner imo):


**3. Write the stylesheet** (`tabs/<name>/<name>.tcss`)

**4. Wire it into the app**

In `tabs/central.py` — add the import:

```python
from .<name>.<name> import MyTab
```

In `main.py` — three things:

1. Add to a category in `TAB_CATEGORIES`
2. Add the tcss path to `CSS_PATH`

```python
# Import
from tabs.central import ..., MyTab

# Category (pick the one that fits)
TAB_CATEGORIES = {
    ...
    "Life & Home": [
        ...
        ("My Module", MyTab("My Module", id="my_module")),
    ],
}

# CSS
CSS_PATH = [..., "./tabs/<name>/<name>.tcss"]
```

**5. (Optional) Add persistence**

- **Document-style data** → save to `file_holders/<module>/`
- **Structured data** → SQLite database at `tabs/<module>/<name>.db`

Every module with a DB usually follows this template (Optional):

```python
import sqlite3
from shared import db_path

DB_PATH = db_path("tabs", "<name>", "<name>.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS ...""")
    conn.commit()
    conn.close()

# CRUD functions follow...
```

---

## Hard rules

These keep the codebase consistent.

### Widget IDs

IDs must follow `<feature>_<descriptor/widget>` — this namespaces them and prevents collisions:

```python
# Nice!
id="alarm_table"
id="timer_start"
id="budget_amount"

# EW!
id="table"
id="start"
id="amount"
```

### `query_one` always takes both arguments

```python
# Nice!
self.query_one("#feature_table", DataTable)
self.query_one("#feature_input", Input)

# EW!
self.query_one("#feature_table")
self.query_one(DataTable)
```

### Modal screens

- **Single action button only if possible** — no "Cancel" button. Users dismiss modals with `Esc` (Optional, I just fine it visually more appealing).
- **Every modal handles Escape** — include an `on_key` handler and a dimmed hint label (Best practice imo):


### CSS color variables


You may use what textual provides  such as : `$accent` `$primary` `$surface` `$boost` `$error` `$text` `$background`.
Or just hard code them for all I care.

### Persistence

New modules that store data must use **only** one of:
- `file_holders/<module>/` — for document-style data (markdown, text, JSON)
- SQLite at `tabs/<module>/<name>.db` — for structured/relational data

No other storage backends "Avoids bs".

### Dependencies

**Don't add new dependencies.** 

Work with Textual, stdlib, and `sqlite3` which should cover about everything "Better not to use a dependency if its not hard for u to make it without".

---

## Module categories

When adding a module, place it in the category that fits best in your opinion:

| Category | Existing modules | Good for |
|---|---|---|
| **Time & Planning** | Clock, Time Zones, Countdown, Job Tracker | Calendars, reminders, scheduling |
| **Writing & Notes** | Note Taker, Todos, Cheat Sheets, Word Counter | Text editing, knowledge management |
| **Finance** | Money Tracker, Budget Tracker | Money, expenses, budgeting |
| **Developer Tools** | JSON Tool, Base Converter, Regex Tester, CSV Viewer, Subnet Calc, Port Checker, Changelog Gen, QR Gen & Extract, Gitignore Builder, Lorem Ipsum | Dev utilities, formatters, generators |
| **Converters & Calc** | Unit Converter, Color Picker, Random Picker | Math, conversion, calculation |
| **Entertainment** | Music, Games, Typing Test | Games, media, fun tools |
| **Life & Home** | Recipe Manager, Habit Tracker | Household, health, personal tracking |

---

## PR checklist

Before opening a pull request:

- [ ] Widget IDs follow `<feature>_<descriptor>`
- [ ] All `query_one` calls pass both `id` and Widget class
- [ ] Modals have Escape handling + dimmed hint label, no Cancel button (Optional)
- [ ] No new dependencies added (Unless have to)
- [ ] Persistence uses only `file_holders/` or SQLite
- [ ] Module is wired into `central.py`, `TAB_CATEGORIES`, and `CSS_PATH`
- [ ] Tested by running `uv run main.py`
- [Name] What OS was this running in
