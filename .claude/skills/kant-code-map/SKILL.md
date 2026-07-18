---
name: kant-code-map
description: Analyze the repository and add/fix KANT tag comments in source code so the IDE can deterministically regenerate the structural code map (a KANT_*.md file at the project root). Only invoke this when the user types the exact command /kant-code-map. Do not invoke it for natural-language phrasing like "update the KANT map" or "generate the map" — wait for the literal command.
---

# KANT Code Map

Usage: `/kant-code-map` — no arguments.

When invoked, for the current project:
1. Analyze the repository and add or correct KANT tag comments above every
   tagged element in source code (see "Code comments" below).
2. Do not create, edit, or hand-compose `KANT_<project-name>.md` yourself —
   KANT IDE regenerates that file deterministically from the source markers
   after your changes are reviewed and applied. Writing it yourself only
   produces a version the IDE immediately overwrites.

## KANT file structure (reference only — the IDE generates this, you don't)

`KANT_<project-name>.md` is a real Markdown document: a title, a `##`
section header, and the map content wrapped in a fenced code block. This is
what the IDE's generator produces from your source markers — shown here so
you understand what your tag comments turn into, not as something to author:

```
[MOD auth/login.py] — login/logout endpoints
- [CLS] UserManager — creates and authenticates users
-- [FN] login — checks credentials, creates session
-- [FN] logout — invalidates current session
[CFG config/database.yaml] — DB connection settings
```

The map is canonical and has no line numbers — it never goes stale, and
exact positions are found by grepping the tag comment in source (e.g.
`grep -rn "\[FN\] login"`), not by reading a number that can drift.

Fixed tag set — do not add others:

| Tag | Element | Path |
|---|---|---|
| MOD | file/module | yes (relative) |
| CFG | config file | yes (relative) |
| CLS | class | no (inherits MOD) |
| TYP | type/interface | no (inherits MOD) |
| FN | function/method | no (inherits MOD/CLS) |
| CST | constant | no |
| VAR | mutable global/state var | no |
| TST | test | path only if standalone file |

## Rules

- Only run on the exact `/kant-code-map` command — never as a side effect of another task, never from paraphrased natural language.
- Cover all real code files; skip assets, binaries, deps (node_modules, venv, .git, dist, build).
- The source code is the single source of truth. The generated map always reflects it — never edit the map to "fix" a mismatch, fix or add the source markers instead.
- Before finishing, re-check your source edits against the most-violated rules below: every tag comment matches its declaration's name; CATEGORY and the tag line agree with OPEN/CLOSED on tag and name; no `[TAG INCOMING]`/`[TAG OUTGOING]` lines were added.

## Code comments

Every tagged element is delimited by an opening marker and a closing marker,
paired by tag + name. These markers are structural bookkeeping only — they
never carry a description and never merge with the category line or the
8-word tag line.

**Opening** (immediately above the element), three lines in this fixed order:

1. **Category line** — general explanation of how the element works:
   `[TAG CATEGORY] Name — how it works`. No length cap.
2. **Tag line** — matches the KANT file exactly:
   `[TAG] Name — description, max 8 words`. This line is the grep anchor.
3. **Open marker** — pure boundary start, no description: `[TAG OPEN] Name`

**Closing** (immediately after the element's last line), one line:

1. `[TAG CLOSED] Name`

There is no INCOMING/OUTGOING line to write. Who calls/uses an element and
what it calls/uses is computed deterministically from the code by KANT IDE's
cross-reference system, not hand-written here — a stale or wrong data-flow
comment is worse than none. Never add `[TAG INCOMING]`/`[TAG OUTGOING]`
lines to new or edited code.

Tag and name in OPEN and CLOSED must match, so the exact span of every
element is recoverable by grep alone, even with nesting.

**Nesting must be strictly well-formed**, like balanced brackets: an OPEN's
matching CLOSED must appear before the CLOSED of whatever element contains
it. Crossing spans are invalid and must be fixed, not left for a tool to
guess at.

RIGHT (properly nested):
```
[CLS OPEN] UserManager
- [FN OPEN] login
- [FN CLOSED] login
[CLS CLOSED] UserManager
```

WRONG (crossing spans — the class closes before its own child does):
```
[CLS OPEN] UserManager
- [FN OPEN] login
[CLS CLOSED] UserManager
- [FN CLOSED] login
```

Example (Python):
```python
# [FN CATEGORY] list_users — paginates using offset = (page-1) * MAX_PAGE_SIZE, capped server-side
# [FN] list_users — GET /users, paginated list
# [FN OPEN] list_users
def list_users(page: int = 1):
    offset = (page - 1) * MAX_PAGE_SIZE
    return db.query(User).limit(MAX_PAGE_SIZE).offset(offset).all()
# [FN CLOSED] list_users

# [FN CATEGORY] create_user — validates payload, hashes password, persists row
# [FN] create_user — POST /users, creates new user
# [FN OPEN] create_user
def create_user(payload: UserCreate):
    ...
# [FN CLOSED] create_user
```

Binding rules:

- Every comment must include the element's name, matching the declaration
  it delimits — unambiguous even out of context.
- The tag line must be byte-identical to the corresponding entry the IDE
  will generate in the KANT map (minus indentation), so grep on either one
  finds the other.
- Every OPEN must have exactly one CLOSED with the same tag and name;
  an unmatched marker is invalid.
- When renaming an element, rename it in all five places in the same edit:
  declaration, category line, tag line, open marker, and closed marker.
