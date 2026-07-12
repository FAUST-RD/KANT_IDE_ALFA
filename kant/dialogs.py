"""Small themed modal dialogs shared by the main window."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QComboBox, QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from kant import theme


class IdeDialogsMixin:
    def _dialog(self, title, message, width=460):
        dialog = QDialog(self)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setMinimumWidth(width)
        dialog.setStyleSheet(
            f'QDialog {{ background:{theme.PANEL}; border:1px solid {theme.BORDER}; }} '
            f'QLabel {{ color:{theme.TEXT}; }}'
        )
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        heading = QLabel(title)
        heading.setFont(QFont('Consolas', theme.TREE_FONT_PT + 2, QFont.DemiBold))
        heading.setStyleSheet(f'color:{theme.WARN};')
        layout.addWidget(heading)
        prompt = QLabel(message)
        prompt.setWordWrap(True)
        layout.addWidget(prompt)
        return dialog, layout

    def _dialog_buttons(self, layout, dialog):
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton('Annulla')
        ok = QPushButton('OK')
        for button in (cancel, ok):
            button.setStyleSheet(theme.BUTTON_STYLE)
            row.addWidget(button)
        cancel.clicked.connect(dialog.reject)
        ok.clicked.connect(dialog.accept)
        layout.addLayout(row)

    def _ide_choice(self, title, message, choices):
        dialog, layout = self._dialog(title, message)
        layout.setSpacing(14)
        result = {'value': None}
        row = QHBoxLayout()
        row.addStretch(1)

        def choose(value):
            result['value'] = value
            dialog.accept()

        for label, value in choices:
            button = QPushButton(label)
            button.setStyleSheet(theme.BUTTON_STYLE)
            button.clicked.connect(lambda _checked=False, selected=value: choose(selected))
            row.addWidget(button)
        layout.addLayout(row)
        return result['value'] if dialog.exec() == QDialog.Accepted else None

    def _ide_yes_no(self, title, message):
        return self._ide_choice(title, message, [('No', False), ('Si', True)]) is True

    def _ide_message(self, title, message):
        self._ide_choice(title, message, [('OK', True)])

    def _ide_text(self, title, label, text=''):
        dialog, layout = self._dialog(title, label)
        field = QLineEdit(text)
        field.setStyleSheet(
            f'background:{theme.CODE_BG}; color:{theme.TEXT}; border:1px solid {theme.BORDER}; '
            f'border-radius:6px; padding:8px;'
        )
        layout.addWidget(field)
        self._dialog_buttons(layout, dialog)
        field.selectAll()
        field.setFocus()
        return (field.text(), True) if dialog.exec() == QDialog.Accepted else ('', False)

    # [FN CATEGORY] _ide_metadata_form — the ⋮ button's metadata editor: one internal window (framed
    # header bar matching the MAPPA dialog's look, not a native title bar) with all three fields
    # together, instead of three sequential single-field prompts.
    # [FN] _ide_metadata_form — tag/name/short-description editor in a single dialog
    # [FN OPEN] _ide_metadata_form
    def _ide_metadata_form(self, tag, name, desc):
        dialog = QDialog(self)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setFixedWidth(420)
        dialog.setStyleSheet(f'QDialog {{ background:{theme.BG}; border:1px solid {theme.BORDER}; }}')

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(34)
        header.setStyleSheet(f'background:{theme.PANEL}; border-bottom:1px solid {theme.BORDER};')
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(14, 0, 8, 0)
        title = QLabel('Metadati KANT')
        title.setFont(QFont('Consolas', theme.CODE_FONT_PT, QFont.DemiBold))
        title.setStyleSheet(f'color:{theme.TEXT}; letter-spacing:2px; border:none;')
        header_row.addWidget(title)
        header_row.addStretch(1)
        close_btn = QPushButton('×')
        close_btn.setFixedSize(26, 24)
        close_btn.setStyleSheet(theme.BUTTON_STYLE)
        close_btn.clicked.connect(dialog.reject)
        header_row.addWidget(close_btn)
        outer.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(18, 16, 18, 16)
        body.setSpacing(10)

        def field_row(label_text, value):
            field_label = QLabel(label_text)
            field_label.setStyleSheet(f'color:{theme.TEXT}; border:none;')
            body.addWidget(field_label)
            field = QLineEdit(value)
            field.setStyleSheet(
                f'background:{theme.CODE_BG}; color:{theme.TEXT}; border:1px solid {theme.BORDER}; '
                f'border-radius:6px; padding:6px;'
            )
            body.addWidget(field)
            return field

        tag_field = field_row('Tag:', tag)
        name_field = field_row('Nome tecnico:', name)
        desc_field = field_row('Descrizione breve:', desc)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton('Annulla')
        ok = QPushButton('OK')
        for button in (cancel, ok):
            button.setStyleSheet(theme.BUTTON_STYLE)
            buttons.addWidget(button)
        cancel.clicked.connect(dialog.reject)
        ok.clicked.connect(dialog.accept)
        body.addLayout(buttons)
        outer.addLayout(body)

        tag_field.selectAll()
        tag_field.setFocus()
        if dialog.exec() != QDialog.Accepted:
            return None
        return tag_field.text(), name_field.text(), desc_field.text()
    # [FN CLOSED] _ide_metadata_form

    # [FN CATEGORY] _ide_agent_choice_form — the /kant-code-map launch prompt: provider, specific
    # model, and reasoning effort together in one internal window instead of a plain 3-button
    # choice, with an explicit Cancel. Model lists and the "no override" sentinel are passed in by
    # the caller (mainwindow.py, which already imports them from widgets.py) rather than imported
    # here, so this stays independent of widgets.py.
    # [FN] _ide_agent_choice_form — provider/model/effort picker with Cancel
    # [FN OPEN] _ide_agent_choice_form
    def _ide_agent_choice_form(self, claude_models, codex_models, model_default):
        dialog = QDialog(self)
        dialog.setModal(True)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setFixedWidth(420)
        dialog.setStyleSheet(f'QDialog {{ background:{theme.BG}; border:1px solid {theme.BORDER}; }}')

        outer = QVBoxLayout(dialog)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QWidget()
        header.setFixedHeight(34)
        header.setStyleSheet(f'background:{theme.PANEL}; border-bottom:1px solid {theme.BORDER};')
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(14, 0, 8, 0)
        title = QLabel('Applica /kant-code-map')
        title.setFont(QFont('Consolas', theme.CODE_FONT_PT, QFont.DemiBold))
        title.setStyleSheet(f'color:{theme.TEXT}; letter-spacing:1px; border:none;')
        header_row.addWidget(title)
        header_row.addStretch(1)
        close_btn = QPushButton('×')
        close_btn.setFixedSize(26, 24)
        close_btn.setStyleSheet(theme.BUTTON_STYLE)
        close_btn.clicked.connect(dialog.reject)
        header_row.addWidget(close_btn)
        outer.addWidget(header)

        body = QVBoxLayout()
        body.setContentsMargins(18, 16, 18, 16)
        body.setSpacing(10)
        combo_style = (
            f'background:{theme.CODE_BG}; color:{theme.TEXT}; border:1px solid {theme.BORDER}; '
            f'border-radius:6px; padding:6px;'
        )

        def field_label(text):
            label = QLabel(text)
            label.setStyleSheet(f'color:{theme.TEXT}; border:none;')
            body.addWidget(label)

        field_label('Provider:')
        provider_combo = QComboBox()
        provider_combo.addItem('Claude Code', 'claude')
        provider_combo.addItem('Codex', 'codex')
        provider_combo.setStyleSheet(combo_style)
        body.addWidget(provider_combo)

        field_label('Modello:')
        model_combo = QComboBox()
        model_combo.setEditable(True)
        model_combo.setStyleSheet(combo_style)
        body.addWidget(model_combo)

        # both CLIs really do have an effort/reasoning-effort parameter (checked against `claude
        # --help` and codex's -c model_reasoning_effort=<level> config override), just under
        # different mechanisms — _agent_command (widgets.py) applies each correctly per provider
        field_label('Effort:')
        effort_combo = QComboBox()
        effort_combo.setEditable(True)
        effort_combo.setStyleSheet(combo_style)
        body.addWidget(effort_combo)
        effort_levels = {
            'claude': (model_default, 'low', 'medium', 'high', 'xhigh', 'max'),
            'codex': (model_default, 'low', 'medium', 'high'),
        }

        def sync_for_provider():
            provider = provider_combo.currentData()
            model_combo.clear()
            model_combo.addItems(codex_models if provider == 'codex' else claude_models)
            effort_combo.clear()
            effort_combo.addItems(effort_levels[provider])

        provider_combo.currentIndexChanged.connect(sync_for_provider)
        sync_for_provider()

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton('Annulla')
        ok = QPushButton('Avvia')
        for button in (cancel, ok):
            button.setStyleSheet(theme.BUTTON_STYLE)
            buttons.addWidget(button)
        cancel.clicked.connect(dialog.reject)
        ok.clicked.connect(dialog.accept)
        body.addLayout(buttons)
        outer.addLayout(body)

        if dialog.exec() != QDialog.Accepted:
            return None
        model = model_combo.currentText().strip()
        effort = effort_combo.currentText().strip()
        return {
            'agent': provider_combo.currentData(),
            'model': None if model in (model_default, '') else model,
            'effort': None if effort in (model_default, '') else effort,
        }
    # [FN CLOSED] _ide_agent_choice_form

    def _ide_item(self, title, label, items):
        if not items:
            return '', False
        dialog, layout = self._dialog(title, label, width=520)
        combo = QComboBox()
        combo.addItems(items)
        combo.setStyleSheet(
            f'background:{theme.CODE_BG}; color:{theme.TEXT}; border:1px solid {theme.BORDER}; '
            f'border-radius:6px; padding:6px;'
        )
        layout.addWidget(combo)
        self._dialog_buttons(layout, dialog)
        return (combo.currentText(), True) if dialog.exec() == QDialog.Accepted else ('', False)
