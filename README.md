# KANT IDE

> **Code already has a structure. KANT makes it visible.**

KANT IDE is a desktop editor that turns structured comments into an explorable map of your codebase. Open a project and move between modules, classes, functions, constants, and tests without losing sight of how they fit together.

It works on ordinary source files and stays out of your runtime:

```text
structured comments  ->  navigable outline  ->  focused editor  ->  project map
```

No custom file format. No generated runtime code. No lock-in.

## Why KANT?

Large files are easy to write and hard to understand. Traditional file trees show where code is stored, but not what is inside each file or how those pieces relate.

KANT adds a small amount of explicit structure where it matters. The IDE uses it to provide:

| Need | KANT IDE |
| --- | --- |
| Understand a large file | Browse its named sections instead of scrolling |
| Work on one responsibility | Open only the relevant function, class, or block |
| Follow dependencies | Inspect deterministic Incoming and Outgoing references |
| See the bigger picture | Explore the codebase in the interactive **MAPPA** view |
| Let an AI edit safely | Review file and hunk changes, then apply or roll back |

## Highlights

### Navigate by meaning

The **Codice** tree is built from KANT markers such as `[FN OPEN]` and `[CLS CLOSED]`. Switch back to **File** whenever you want a conventional folder view.

### Edit without losing context

Open a single tagged section in a focused editor. Changes update the original source file through atomic autosaves, with undo/redo and external-change detection.

### Explore relationships

Incoming/Outgoing panels show what crosses a section's boundary. **MAPPA** turns the same deterministic reference graph into a filterable, draggable view with module clustering and drill-down.

### Bring your existing tools

KANT IDE includes Git actions, a terminal, lightweight syntax checks, optional LSP integration, and Python debugging. Claude Code and Codex can run inside the IDE with permission prompts, snapshots, change review, and rollback.

## How the KANT convention works

KANT describes the structure of a codebase with ordinary comments. The source remains valid for its language and continues to work with normal editors, compilers, formatters, and version control.

A section can use four markers:

```text
[TAG CATEGORY] detailed purpose or architectural context
[TAG] short description shown in the IDE
[TAG OPEN #stable-id] exact-name
...section source code...
[TAG CLOSED #stable-id] exact-name
```

- `TAG` identifies the kind of element. Common tags are `MOD` (module), `CLS` (class), `FN` (function), `TYP` (type), `CST` (constant), `VAR` (variable), `CFG` (configuration), and `TST` (test).
- `CATEGORY` is optional long-form context. It is useful for explaining responsibility, assumptions, or relationships that are not obvious from the code.
- `[TAG]` is an optional concise description used as the human-readable label in the project tree and map.
- `OPEN` starts the section and `CLOSED` ends it. Their tag, name, and optional ID must match.
- `#stable-id` lets the IDE recognize the same section across reparses and name edits. KANT IDE automatically adds an ID when an older marker does not have one.

Sections can be nested. For example, functions can live inside a class and classes inside a module. They must close in reverse order: the most recently opened section is always closed first.

```python
# [MOD] User service
# [MOD OPEN #users-module] users.py

# [CLS CATEGORY] Coordinates user retrieval without owning persistence
# [CLS] User service
# [CLS OPEN #user-service] UserService
class UserService:
    # [FN CATEGORY] Reads one user through the injected repository
    # [FN] Fetch user by ID
    # [FN OPEN #load-user] load_user
    def load_user(self, user_id):
        return self.repository.get(user_id)
    # [FN CLOSED #load-user] load_user
# [CLS CLOSED #user-service] UserService

# [MOD CLOSED #users-module] users.py
```

Marker lines may use the host language's normal comment syntax, including `#`, `//`, `--`, `;`, `/* ... */`, and `<!-- ... -->`. KANT IDE preserves marker text and all unedited source while converting the marked regions into its navigable outline.

## Installation

KANT IDE requires Python 3 and PySide6.

```powershell
git clone https://github.com/FAUST-RD/KANT_IDE.git
cd KANT_IDE
python -m pip install -r requirements.txt
python kant_editor.py
```

On Linux or macOS, `./install.sh` installs the Python dependency and prints the launch command.

Language-server features are enabled only when a compatible server is already available on `PATH`. The editor itself works without one.

## A first five-minute tour

1. Launch `kant_editor.py` and open a project folder.
2. Open any source file. Untagged files remain editable as normal.
3. Add `OPEN` and `CLOSED` markers around one useful function or class.
4. Select **Codice** and open the new section directly from the project tree.
5. Use **INCOMING**, **OUTGOING**, and **MAPPA** to explore its relationships.

Start small: KANT does not require tagging an entire project before it becomes useful. The legacy `index.html` prototype is kept for reference; current development targets the Python application.

## Development

- [`PROJECT_MAP.md`](PROJECT_MAP.md) explains where each feature lives and how the main flows connect.
- [`DESIGN.md`](DESIGN.md) records architectural decisions and safety invariants.
- [`AGENTS.md`](AGENTS.md) contains repository instructions for AI coding agents.

Run the regression check without opening a window:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python test_kant_smoke.py
```

On Linux or macOS, use `export QT_QPA_PLATFORM=offscreen` before the test command.

## License

[MIT](LICENSE)
