from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Button, Label, Select, DataTable
from textual.widget import Widget
from textual.containers import Horizontal, Vertical
from textual.binding import Binding

from .db import (
    init_db, seed_defaults, get_accounts,
    get_categories,
    add_transaction, get_transactions, delete_transaction,
    get_summary, get_distinct_months,
)
from .modals import MoneyDeleteConfirmModal, MoneyManageModal


class MoneyWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("n", "add_transaction", "Add Transaction"),
        Binding("d", "delete_transaction", "Delete Transaction"),
        Binding("m", "manage", "Manage Accounts/Categories"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_month = None
        self._current_account = None

    def compose(self) -> ComposeResult:
        with Vertical(id="money_container"):
            with Horizontal(id="money_summary_row"):
                with Vertical(id="money_card_balance"):
                    yield Label("Total Balance", id="money_card_balance_label")
                    yield Label("$0.00", id="money_card_balance_value")
                with Vertical(id="money_card_income"):
                    yield Label("Income", id="money_card_income_label")
                    yield Label("$0.00", id="money_card_income_value")
                with Vertical(id="money_card_expenses"):
                    yield Label("Expenses", id="money_card_expenses_label")
                    yield Label("$0.00", id="money_card_expenses_value")

            with Horizontal(id="money_input_row"):
                yield Input(placeholder="YYYY-MM-DD", id="money_date")
                yield Select(
                    [("Income", "income"), ("Expense", "expense")],
                    value="expense", allow_blank=False, id="money_type"
                )
                yield Input(placeholder="Amount", id="money_amount")
                yield Select([], id="money_category", prompt="Category")
                yield Select([], id="money_account", prompt="Account")
                yield Input(placeholder="Note (optional)", id="money_note")
                yield Button("Add", variant="primary", id="money_add_btn")

            with Horizontal(id="money_filter_row"):
                yield Select(
                    [("All Months", "")], value="", allow_blank=False,
                    id="money_month_filter"
                )
                yield Select(
                    [("All Accounts", "")], value="", allow_blank=False,
                    id="money_account_filter"
                )
                yield Button("Manage", id="money_manage_btn")

            yield DataTable(id="money_table")

            yield Label("Spending by Category", id="money_breakdown_heading")
            yield DataTable(id="money_cat_breakdown")

    def on_mount(self):
        init_db()
        seed_defaults()

        self.query_one("#money_date", Input).value = datetime.now().strftime("%Y-%m-%d")

        table = self.query_one("#money_table", DataTable)
        table.add_columns("Date", "Type", "Category", "Account", "Amount", "Note")
        table.cursor_type = "row"
        table.tooltip = "n: Add  d: Delete  m: Manage"

        cat_table = self.query_one("#money_cat_breakdown", DataTable)
        cat_table.add_columns("Category", "Amount", "% of Total")

        self._refresh_account_select()
        self._refresh_category_select()
        self._refresh_month_filter()
        self._refresh_account_filter()
        self._refresh_all()

    def on_select_changed(self, event: Select.Changed):
        sid = event.select.id
        if sid == "money_type":
            self._refresh_category_select()
        elif sid == "money_month_filter":
            val = event.select.value
            if val == Select.BLANK or val == Select.NULL:
                return
            new_month = val if val else None
            if new_month == self._current_month:
                return
            self._current_month = new_month
            self._refresh_all()
        elif sid == "money_account_filter":
            val = event.select.value
            if val == Select.BLANK or val == Select.NULL:
                return
            new_acct = int(val) if val else None
            if new_acct == self._current_account:
                return
            self._current_account = new_acct
            self._refresh_all()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "money_add_btn":
            self.action_add_transaction()
        elif pid == "money_manage_btn":
            self.action_manage()

    def action_add_transaction(self):
        date_val = self.query_one("#money_date", Input).value.strip()
        txn_type = self.query_one("#money_type", Select).value
        amount_str = self.query_one("#money_amount", Input).value.strip()
        cat_val = self.query_one("#money_category", Select).value
        acct_val = self.query_one("#money_account", Select).value
        note = self.query_one("#money_note", Input).value.strip()

        if not date_val:
            self.notify("Date is required.", severity="error")
            return
        try:
            date_val = datetime.strptime(date_val, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            self.notify("Invalid date. Use YYYY-MM-DD format.", severity="error")
            return
        if not amount_str:
            self.notify("Amount is required.", severity="error")
            return
        try:
            amount = float(amount_str)
        except ValueError:
            self.notify("Amount must be a number.", severity="error")
            return
        if amount <= 0:
            self.notify("Amount must be positive.", severity="error")
            return
        if cat_val == Select.BLANK or cat_val == Select.NULL:
            self.notify("Please select a category.", severity="error")
            return
        if acct_val == Select.BLANK or acct_val == Select.NULL:
            self.notify("Please select an account.", severity="error")
            return

        add_transaction(date_val, amount, txn_type, int(acct_val), int(cat_val), note)

        self.query_one("#money_amount", Input).value = ""
        self.query_one("#money_note", Input).value = ""
        self._refresh_all()

    def action_delete_transaction(self):
        table = self.query_one("#money_table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            txn_id = int(row_key)
            txn = get_transactions()
            info = ""
            for t in txn:
                if t["id"] == txn_id:
                    info = f"Delete transaction?\n\n[dim]${t['amount']:,.2f} — {t['category_name']} ({t['date']})[/]"
                    break
            self.app.push_screen(
                MoneyDeleteConfirmModal(info),
                lambda result: self._on_delete(txn_id, result)
            )
        except (IndexError, ValueError):
            pass

    def _on_delete(self, txn_id, confirmed):
        if confirmed:
            delete_transaction(txn_id)
            self._refresh_all()

    def action_manage(self):
        self.app.push_screen(MoneyManageModal(), self._on_manage_done)

    def _on_manage_done(self, _):
        self._refresh_account_select()
        self._refresh_category_select()
        self._refresh_all()

    def _refresh_all(self):
        self._refresh_table()
        self._refresh_summary()
        self._refresh_category_breakdown()
        self._refresh_month_filter()
        self._refresh_account_filter()

    def _refresh_table(self):
        table = self.query_one("#money_table", DataTable)
        table.clear()
        rows = get_transactions(
            month=self._current_month,
            account_id=self._current_account,
        )
        for txn in rows:
            table.add_row(
                txn["date"],
                txn["type"].capitalize(),
                txn["category_name"],
                txn["account_name"],
                f"${txn['amount']:,.2f}",
                txn["note"][:30],
                key=str(txn["id"]),
            )

    def _refresh_summary(self):
        s = get_summary(month=self._current_month, account_id=self._current_account)
        bal_label = self.query_one("#money_card_balance_value", Label)
        bal_label.update(f"${s['net_balance']:,.2f}")
        if s["net_balance"] < 0:
            bal_label.add_class("negative")
        else:
            bal_label.remove_class("negative")
        self.query_one("#money_card_income_value", Label).update(f"${s['total_income']:,.2f}")
        self.query_one("#money_card_expenses_value", Label).update(f"${s['total_expenses']:,.2f}")

    def _refresh_category_breakdown(self):
        table = self.query_one("#money_cat_breakdown", DataTable)
        table.clear()
        s = get_summary(month=self._current_month, account_id=self._current_account)
        total = s["total_expenses"] if s["total_expenses"] > 0 else 1
        for cat in s["category_breakdown"]:
            if cat["total"] > 0:
                pct = (cat["total"] / total) * 100
            else:
                pct = 0
            table.add_row(cat["name"], f"${cat['total']:,.2f}", f"{pct:.1f}%")

    def _refresh_account_select(self):
        sel = self.query_one("#money_account", Select)
        accounts = get_accounts()
        sel.set_options([(a["name"], str(a["id"])) for a in accounts])

    def _refresh_category_select(self):
        sel = self.query_one("#money_category", Select)
        txn_type = self.query_one("#money_type", Select).value
        if txn_type == Select.BLANK or txn_type == Select.NULL:
            txn_type = "expense"
        cats = get_categories(cat_type=txn_type)
        sel.set_options([(c["name"], str(c["id"])) for c in cats])

    def _refresh_month_filter(self):
        sel = self.query_one("#money_month_filter", Select)
        current = self._current_month if self._current_month else ""
        months = get_distinct_months()
        options = [("All Months", "")]
        for m in months:
            if m is None:
                continue
            try:
                label = datetime.strptime(m, "%Y-%m").strftime("%B %Y")
            except (ValueError, TypeError):
                label = m
            options.append((label, m))
        sel.set_options(options)
        sel.value = current

    def _refresh_account_filter(self):
        sel = self.query_one("#money_account_filter", Select)
        current = str(self._current_account) if self._current_account else ""
        accounts = get_accounts()
        options = [("All Accounts", "")]
        for a in accounts:
            options.append((a["name"], str(a["id"])))
        sel.set_options(options)
        sel.value = current


class MoneyTab(TabPane):
    def compose(self) -> ComposeResult:
        yield MoneyWidget()
