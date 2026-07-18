"""Cross-file element groupings — deterministic, no Qt, mirrors kant/pyenv.py's own boundary.

A grouping is an arbitrary, named collection of KANT elements (any tag — MOD/CLS/FN/TYP/CST/VAR/
CFG/TST — parent or child indifferently, from any file) bundled together independent of the
source tree's own nesting. Persisted as .kant/groupings.json, the same project-config directory
kant/pyenv.py's python.json already established as the convention for "project state that isn't
source content". Members are stored as xref-style keys ('<rel_path>::<uid>', see kant/xref.py's
XrefElement.key) — the same identifier the existing cross-reference graph and _navigate_to_element
already resolve, so a grouping's members are navigable for free, with no new lookup machinery.
"""
import json
import secrets
from dataclasses import dataclass, field, asdict
from pathlib import Path


CONFIG_DIRNAME = '.kant'
CONFIG_FILENAME = 'groupings.json'


# [TYP] Grouping — one named, arbitrary bundle of element keys
# [TYP OPEN] Grouping
@dataclass
class Grouping:
    id: str
    name: str
    members: list = field(default_factory=list)  # xref-style keys, '<rel_path>::<uid>'
# [TYP CLOSED] Grouping


def config_path(project_root):
    return Path(project_root) / CONFIG_DIRNAME / CONFIG_FILENAME


# [FN] load_groupings — every grouping saved for project_root, or [] if none/unreadable
# [FN OPEN] load_groupings
def load_groupings(project_root):
    try:
        data = json.loads(config_path(project_root).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    groups = data.get('groups', [])
    return [Grouping(id=g['id'], name=g['name'], members=list(g.get('members', ()))) for g in groups if g.get('id') and g.get('name')]
# [FN CLOSED] load_groupings


# [FN] save_groupings — writes every grouping for project_root to .kant/groupings.json
# [FN OPEN] save_groupings
def save_groupings(project_root, groupings):
    path = config_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {'groups': [asdict(g) for g in groupings]}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
# [FN CLOSED] save_groupings


def new_grouping(name):
    return Grouping(id=secrets.token_hex(4), name=name.strip())


# [FN] add_member — adds a key to a grouping (by id) if not already present, saves, returns the
# updated list; a pure convenience wrapper so callers don't hand-roll the load/mutate/save sequence
# [FN OPEN] add_member
def add_member(project_root, group_id, key):
    groupings = load_groupings(project_root)
    for grouping in groupings:
        if grouping.id == group_id:
            if key not in grouping.members:
                grouping.members.append(key)
            break
    save_groupings(project_root, groupings)
    return groupings
# [FN CLOSED] add_member


# [FN CATEGORY] remap_member_key — rewrites the rel_path portion of one xref-style key
# ('<rel_path>::<uid>') when it falls under old_rel, leaving the uid untouched. For a file rename
# (is_dir=False) only an exact rel_path match qualifies; for a folder rename (is_dir=True) both the
# folder's own key (rare — groupings hold elements, which live inside files, not bare folders) and
# every key nested under it qualify, mirroring the same old_path/os.sep prefix test
# kant/workspace.py:_rename_tree_item already uses to find affected open tabs. Pure and total: a key
# that doesn't match old_rel is returned unchanged, so a caller can map this over every member
# without a separate "does this apply" branch, and a second call with the same (old_rel, new_rel)
# after the first is a no-op — nothing left starts with old_rel anymore.
# [FN] remap_member_key — key with its rel_path rewritten if under old_rel, else key unchanged
# [FN OPEN] remap_member_key
def remap_member_key(key, old_rel, new_rel, is_dir):
    if '::' not in key:
        return key
    rel, uid = key.rsplit('::', 1)
    if is_dir:
        if rel == old_rel:
            new_path = new_rel
        elif rel.startswith(old_rel + '/'):
            new_path = new_rel + rel[len(old_rel):]
        else:
            return key
    elif rel != old_rel:
        return key
    else:
        new_path = new_rel
    return f'{new_path}::{uid}'
# [FN CLOSED] remap_member_key


# [FN CATEGORY] migrate_member_paths — after KANT IDE renames a file or folder, updates every
# Grouping member key whose path fell under the old name, preserving the uid and leaving unrelated
# members untouched. Saves only if something actually changed (idempotent: a repeat call with the
# same old_rel/new_rel finds nothing left to remap and skips the write).
# [FN] migrate_member_paths — remaps Groupings member keys after a rename; True if anything changed
# [FN OPEN] migrate_member_paths
def migrate_member_paths(project_root, old_rel, new_rel, is_dir):
    groupings = load_groupings(project_root)
    changed = False
    for grouping in groupings:
        # dict.fromkeys dedupes while preserving order — if two distinct old keys ever remapped onto
        # the same new key (a rename target colliding with an existing member), keep one entry
        # instead of a stray duplicate; mirrors migrate_position_keys' own collision handling below
        remapped = list(dict.fromkeys(remap_member_key(key, old_rel, new_rel, is_dir) for key in grouping.members))
        if remapped != grouping.members:
            grouping.members = remapped
            changed = True
    if changed:
        save_groupings(project_root, groupings)
    return changed
# [FN CLOSED] migrate_member_paths
