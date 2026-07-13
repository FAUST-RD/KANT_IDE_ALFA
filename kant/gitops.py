"""Git actions mixed into MainWindow: status refresh, diff/stage, commit, and branch switch.

AI navigation: every method here shells out to the real `git` CLI (via `_run_git`) rather than
parsing .git internals. `self.git_root`/`self.git_status` are set by `_refresh_git_status` and
read (not owned) here; the tree/status-badge rendering that consumes them stays in mainwindow.py.
"""
import os
import subprocess

from kant.gitutil import find_git_root, git_status_map


# [CLS CATEGORY] GitOpsMixin — mixed into MainWindow (alongside IdeDialogsMixin, WorkspaceMixin)
# so git actions live in their own file instead of growing mainwindow.py further; every method
# still reaches MainWindow state (self.git_root, self.terminal, self._run_background, etc.) the
# same as if it were defined directly on the class.
# [CLS] GitOpsMixin — git status/diff/stage/commit/branch actions for MainWindow
# [CLS OPEN] GitOpsMixin
class GitOpsMixin:
    def _refresh_git_status(self):
        if self._git_refresh_pending or not self.project_root_path:
            return
        project_root = self.project_root_path
        self._git_refresh_pending = True

        def read_status():
            git_root = find_git_root(project_root)
            return git_root, git_status_map(git_root)

        def apply_status(result, error):
            self._git_refresh_pending = False
            if self.project_root_path != project_root:
                self._refresh_git_status()
                return
            if error:
                return
            self.git_root, self.git_status = result
            self._update_action_buttons()
            self._rebuild_tree(refresh_git=False)

        self._run_background(read_status, apply_status)

    def _git_status_for_path(self, path):
        if not self.git_root:
            return ''
        rel = os.path.relpath(path, self.git_root)
        return self.git_status.get(rel, '')

    def _git_status_for_dir(self, path):
        if not self.git_root:
            return ''
        rel = os.path.relpath(path, self.git_root)
        prefix = '' if rel == '.' else rel + os.sep
        return 'M' if any(p.startswith(prefix) for p in self.git_status) else ''

    def _git_relpath(self, path):
        if not self.git_root or not path:
            return None
        return os.path.relpath(path, self.git_root)

    def _run_git(self, args, git_root=None):
        git_root = git_root or self.git_root
        if not git_root:
            return None
        return subprocess.run(
            ['git', '-C', git_root, *args],
            capture_output=True,
            text=True,
            timeout=8,
        )

    def _git_diff_file(self, path):
        rel = self._git_relpath(path)
        if not rel:
            return
        git_root = self.git_root
        def diff():
            result = self._run_git(['diff', '--', rel], git_root)
            text = result.stdout.strip() if result else ''
            if not text:
                cached = self._run_git(['diff', '--cached', '--', rel], git_root)
                text = cached.stdout.strip() if cached else ''
            return text

        self._run_background(
            diff,
            lambda text, error: self.terminal.write_info(
                f'\n# git diff -- {rel}\n{("Errore: " + str(error)) if error else (text or "Nessuna differenza")}\n'
            ),
        )

    def _git_stage_file(self, path, staged):
        rel = self._git_relpath(path)
        if not rel:
            return
        args = ['add', '--', rel] if staged else ['restore', '--staged', '--', rel]
        action = 'stage' if staged else 'unstage'
        git_root = self.git_root

        def done(result, error):
            if error or result is None or result.returncode:
                message = str(error) if error else ((result.stderr or result.stdout) if result else 'Git non disponibile')
                self.terminal.write_info(f'\n# git {action} {rel}\n{message}\n')
                return
            self._refresh_after_fs_change()
            self.terminal.write_info(f'\n# git {action} {rel}: OK\n')

        self._run_background(lambda: self._run_git(args, git_root), done)

    def _active_file_path(self):
        tab = self.active_tab
        return tab.path if tab is not None else None

    def _git_refresh(self):
        self._refresh_after_fs_change()
        self.terminal.write_info('\n# Git refresh: OK\n')

    def _git_diff_active_file(self):
        path = self._active_file_path()
        if path:
            self._git_diff_file(path)

    def _git_stage_active_file(self):
        path = self._active_file_path()
        if path:
            self._git_stage_file(path, staged=True)

    def _git_unstage_active_file(self):
        path = self._active_file_path()
        if path:
            self._git_stage_file(path, staged=False)

    # [FN CATEGORY] _git_commit — reads the staged-file list fresh (git diff --cached --name-only)
    # before opening the dialog rather than trusting self.git_status, since that map collapses " M"
    # (unstaged) and "M " (staged) to the same single-char code and can't tell them apart.
    # [FN] _git_commit — opens the commit dialog and runs `git commit -m`
    # [FN OPEN] _git_commit
    def _git_commit(self):
        if not self.git_root:
            return
        result = self._run_git(['diff', '--cached', '--name-only'])
        staged = [line for line in (result.stdout.splitlines() if result else []) if line.strip()]
        message = self._ide_git_commit_form(staged)
        if not message:
            return
        result = self._run_git(['commit', '-m', message])
        if result is None or result.returncode:
            error = (result.stderr or result.stdout) if result else 'Git non disponibile'
            self.terminal.write_info(f'\n# git commit\n{error}\n')
            return
        self._refresh_after_fs_change()
        self.terminal.write_info(f'\n# git commit: OK\n{result.stdout}\n')
    # [FN CLOSED] _git_commit

    # [FN CATEGORY] _git_switch_branch — lists local branches (git branch --format), reuses the
    # existing combo-box picker dialog (_ide_item) instead of a bespoke one, then checks out the pick.
    # [FN] _git_switch_branch — branch picker + `git checkout`
    # [FN OPEN] _git_switch_branch
    def _git_switch_branch(self):
        if not self.git_root:
            return
        result = self._run_git(['branch', '--format=%(refname:short)'])
        branches = [line.strip() for line in (result.stdout.splitlines() if result else []) if line.strip()]
        if not branches:
            self.terminal.write_info('\n# git branch\nNessun branch trovato\n')
            return
        branch, ok = self._ide_item('Cambia branch', 'Branch:', branches)
        if not ok or not branch:
            return
        result = self._run_git(['checkout', branch])
        if result is None or result.returncode:
            error = (result.stderr or result.stdout) if result else 'Git non disponibile'
            self.terminal.write_info(f'\n# git checkout {branch}\n{error}\n')
            return
        self._refresh_after_fs_change()
        self.terminal.write_info(f'\n# git checkout {branch}: OK\n')
    # [FN CLOSED] _git_switch_branch
# [CLS CLOSED] GitOpsMixin
