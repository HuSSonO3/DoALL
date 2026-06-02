from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Select, DataTable
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen

from .db import (
    add_account, delete_account, get_account_txn_count, get_accounts,
    add_category, delete_category, get_category_txn_count, get_categories,
)


class MoneyDeleteConfirmModal(ModalScreen):
    """Confirm before deleting."""

    def __init__(self, message: str):
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Container(id="money_delete_container"):
            yield Label(self._message, id="money_delete_label")
            with Horizontal(id="money_delete_buttons"):
                yield Button("Delete", variant="error", id="money_delete_confirm")
            yield Label("Press Escape to close", id="money_small_label")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "money_delete_confirm":
            self.dismiss(True)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)


class MoneyManageModal(ModalScreen):
    """Manage accounts and categories."""

    def compose(self) -> ComposeResult:
        with Container(id="money_manage_container"):
            yield Label("[bold]Manage Accounts & Categories[/]", id="money_manage_title")
            yield Label("Press Escape to close", id="money_small_label")

            # ── Accounts section ──
            yield Label("Accounts", id="money_manage_section")
            with Horizontal(id="money_manage_acct_row"):
                yield Input(placeholder="New account name...", id="money_new_acct_name")
                yield Button("Add Account", variant="primary", id="money_add_acct_btn")
            yield DataTable(id="money_manage_acct_table")
            with Horizontal(id="money_manage_acct_actions"):
                yield Button("Delete Selected Account", variant="error", id="money_del_acct_btn")

            # ── Categories section ──
            yield Label("Categories", id="money_manage_section2")
            with Horizontal(id="money_manage_cat_row"):
                yield Input(placeholder="New category name...", id="money_new_cat_name")
                yield Select(
                    [("Income", "income"), ("Expense", "expense")],
                    value="expense", allow_blank=False, id="money_new_cat_type"
                )
                yield Button("Add Category", variant="primary", id="money_add_cat_btn")
            yield DataTable(id="money_manage_cat_table")
            with Horizontal(id="money_manage_cat_actions"):
                yield Button("Delete Selected Category", variant="error", id="money_del_cat_btn")

    def on_mount(self):
        self._refresh_accounts()
        self._refresh_categories()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "money_add_acct_btn":
            name = self.query_one("#money_new_acct_name", Input).value.strip()
            if name:
                result = add_account(name)
                if result:
                    self.query_one("#money_new_acct_name", Input).value = ""
                    self._refresh_accounts()
                else:
                    self.notify("Account name already exists.", severity="error")
        elif pid == "money_add_cat_btn":
            name = self.query_one("#money_new_cat_name", Input).value.strip()
            cat_type = self.query_one("#money_new_cat_type", Select).value
            if name:
                result = add_category(name, cat_type)
                if result:
                    self.query_one("#money_new_cat_name", Input).value = ""
                    self._refresh_categories()
                else:
                    self.notify("Category name already exists.", severity="error")
        elif pid == "money_del_acct_btn":
            self._delete_selected("acct")
        elif pid == "money_del_cat_btn":
            self._delete_selected("cat")

    def _delete_selected(self, kind):
        if kind == "acct":
            table = self.query_one("#money_manage_acct_table", DataTable)
        else:
            table = self.query_one("#money_manage_cat_table", DataTable)
        if table.row_count == 0:
            self.notify("No item selected.", severity="error")
            return

        row = table.cursor_row
        if row < 0 or row >= len(table.ordered_rows):
            self.notify("Please select a row first.", severity="error")
            return

        row_key = table.ordered_rows[row].key.value
        if row_key is None:
            self.notify("Could not identify selected item.", severity="error")
            return

        row_id = int(row_key)
        if kind == "acct":
            count = get_account_txn_count(row_id)
            label = "account"
        else:
            count = get_category_txn_count(row_id)
            label = "category"

        if count > 0:
            msg = (
                f"Delete this {label}?\n\n"
                f"[dim]It has [bold]{count}[/] transaction(s) "
                f"which will also be deleted.[/]"
            )
        else:
            msg = f"Delete this {label}?"

        self.app.push_screen(
            MoneyDeleteConfirmModal(msg),
            lambda confirmed: self._do_delete(kind, row_id, confirmed)
        )

    def _do_delete(self, kind, row_id, confirmed):
        if not confirmed:
            return
        if kind == "acct":
            deleted = delete_account(row_id, force=True)
        else:
            deleted = delete_category(row_id, force=True)

        if deleted:
            if kind == "acct":
                self._refresh_accounts()
            else:
                self._refresh_categories()
        else:
            self.notify("Could not delete.", severity="error")

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(True)

    def _refresh_accounts(self):
        table = self.query_one("#money_manage_acct_table", DataTable)
        table.clear()
        if not table.columns:
            table.add_columns("Name", "Type", "Balance")
            table.cursor_type = "row"
        for acct in get_accounts():
            table.add_row(
                acct["name"], acct["type"],
                f"${acct['balance']:,.2f}",
                key=str(acct["id"])
            )

    def _refresh_categories(self):
        table = self.query_one("#money_manage_cat_table", DataTable)
        table.clear()
        if not table.columns:
            table.add_columns("Name", "Type")
            table.cursor_type = "row"
        for cat in get_categories():
            table.add_row(
                cat["name"], cat["type"].capitalize(),
                key=str(cat["id"])
            )
