"""Modal screens for the Budget Tracker module."""

from textual.app import ComposeResult
from textual.widgets import Input, Button, Label, Select, DataTable
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.binding import Binding

from .db import (
    get_total_budget, get_category_sum,
    get_budget_transactions, delete_budget_transaction,
)


# ═══════════════════════════════════════════════════════════════
# Set Total Budget Modal
# ═══════════════════════════════════════════════════════════════

class BudgetSetTotalModal(ModalScreen):
    """Set the total monthly budget amount."""

    def __init__(self, budget_id: int, current: float):
        super().__init__()
        self._budget_id = budget_id
        self._current = current

    def compose(self) -> ComposeResult:
        with Container(id="budget_total_container"):
            yield Label("[bold]Set Monthly Budget[/]", id="budget_total_title")
            yield Label(
                f"Current budget: ${self._current:,.2f}\n"
                f"Allocated to categories: ${get_category_sum(self._budget_id):,.2f}",
                id="budget_total_info"
            )
            yield Input(
                placeholder="Enter total budget amount...",
                value=str(self._current) if self._current > 0 else "",
                id="budget_total_input"
            )
            with Horizontal(id="budget_total_buttons"):
                yield Button("Save", variant="primary", id="budget_total_save")
            yield Label("Press Escape to close", id="budget_small_label")

    def _try_save(self):
        val = self.query_one("#budget_total_input", Input).value.strip()
        if not val:
            self.notify("Please enter an amount.", severity="error")
            return
        try:
            amount = float(val)
        except ValueError:
            self.notify("Amount must be a number.", severity="error")
            return
        if amount <= 0:
            self.notify("Budget must be positive.", severity="error")
            return
        self.dismiss(amount)

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "budget_total_save":
            self._try_save()

    def on_input_submitted(self, event: Input.Submitted):
        self._try_save()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)


# ═══════════════════════════════════════════════════════════════
# Add Category Form Modal
# ═══════════════════════════════════════════════════════════════

class BudgetCategoryFormModal(ModalScreen):
    """Add a new budget category envelope."""

    def __init__(self, budget_id: int):
        super().__init__()
        self._budget_id = budget_id

    def compose(self) -> ComposeResult:
        total_budget = get_total_budget(self._budget_id)
        available = total_budget - get_category_sum(self._budget_id)

        with Container(id="budget_cat_form_container"):
            yield Label(
                f"[bold]Add Budget Category[/]  [dim](available: ${available:,.2f})[/]",
                id="budget_cat_form_title"
            )
            yield Label("Category Name")
            yield Input(placeholder="e.g. Food, Rent, Entertainment...", id="budget_cat_name_input")
            yield Label("Budget Amount (only for Decrease)")
            yield Input(placeholder="Leave empty for Increase/Stagnant...", id="budget_cat_amount_input")
            yield Label("Budget Impact")
            yield Select(
                [("Decrease — allocate from total budget", "decrease"),
                 ("Increase — transactions add to total", "increase"),
                 ("Stagnant — tracking only, no budget effect", "stagnant")],
                value="decrease", allow_blank=False, id="budget_cat_impact"
            )
            with Horizontal(id="budget_cat_form_buttons"):
                yield Button("Save", variant="primary", id="budget_cat_save")

    def _try_save(self):
        name = self.query_one("#budget_cat_name_input", Input).value.strip()
        amount_str = self.query_one("#budget_cat_amount_input", Input).value.strip()
        impact = self.query_one("#budget_cat_impact", Select).value

        if not name:
            self.notify("Category name is required.", severity="error")
            return

        if amount_str:
            try:
                amount = float(amount_str)
            except ValueError:
                self.notify("Amount must be a number.", severity="error")
                return
            if amount < 0:
                self.notify("Amount cannot be negative.", severity="error")
                return
        else:
            amount = 0.0

        if impact == "decrease":
            if amount <= 0:
                self.notify("Decrease categories need a budget amount > 0.", severity="error")
                return
            total_budget = get_total_budget(self._budget_id)
            reserved = get_category_sum(self._budget_id)
            available = total_budget - reserved
            if amount > available:
                self.notify(
                    f"Not enough budget. ${reserved:,.2f} already reserved "
                    f"from ${total_budget:,.2f} (only ${available:,.2f} available).",
                    severity="error"
                )
                return
        else:
            amount = 0.0

        self.dismiss({"name": name, "amount": amount, "impact": impact})

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "budget_cat_save":
            self._try_save()

    def on_input_submitted(self, event: Input.Submitted):
        self._try_save()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)


# ═══════════════════════════════════════════════════════════════
# Delete Transaction Confirm Modal
# ═══════════════════════════════════════════════════════════════

class BudgetDeleteConfirmModal(ModalScreen):
    """Confirm before deleting a transaction."""

    def __init__(self, txn_info: str):
        super().__init__()
        self._txn_info = txn_info

    def compose(self) -> ComposeResult:
        with Container(id="budget_del_container"):
            yield Label(f'Delete transaction?\n\n[dim]{self._txn_info}[/]', id="budget_del_label")
            with Horizontal(id="budget_del_buttons"):
                yield Button("Delete", variant="error", id="budget_del_confirm")
            yield Label("Press Escape to close", id="budget_small_label")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "budget_del_confirm":
            self.dismiss(True)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)


# ═══════════════════════════════════════════════════════════════
# Delete Category Confirm Modal
# ═══════════════════════════════════════════════════════════════

class BudgetDeleteCategoryConfirmModal(ModalScreen):
    """Confirm before deleting a budget category."""

    def __init__(self, cat_name: str, txn_count: int = 0):
        super().__init__()
        self._cat_name = cat_name
        self._txn_count = txn_count

    def compose(self) -> ComposeResult:
        warning = ""
        if self._txn_count > 0:
            warning = (
                f"\n[dim]({self._txn_count} transaction{'s' if self._txn_count != 1 else ''} "
                f"in this category will also be deleted)[/]"
            )
        with Container(id="budget_cat_del_container"):
            yield Label(
                f'Delete category "[bold]{self._cat_name}[/]"?{warning}',
                id="budget_cat_del_label"
            )
            with Horizontal(id="budget_cat_del_buttons"):
                yield Button("Delete", variant="error", id="budget_cat_del_confirm")
            yield Label("Press Escape to close", id="budget_small_label")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "budget_cat_del_confirm":
            self.dismiss(True)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)


# ═══════════════════════════════════════════════════════════════
# Category Transactions Detail Modal
# ═══════════════════════════════════════════════════════════════

class BudgetCategoryTransactionsModal(ModalScreen):
    """View all transactions for a specific category."""

    BINDINGS = [
        Binding("d", "delete_txn", "Delete Transaction"),
    ]

    def __init__(self, budget_id: int, cat_id: int, cat_name: str, month_label: str):
        super().__init__()
        self._budget_id = budget_id
        self._cat_id = cat_id
        self._cat_name = cat_name
        self._month_label = month_label

    def compose(self) -> ComposeResult:
        with Container(id="budget_cat_txn_container"):
            yield Label(
                f"[bold]{self._cat_name}[/] — {self._month_label}",
                id="budget_cat_txn_title"
            )
            yield DataTable(id="budget_cat_txn_table")
            yield Label("", id="budget_cat_txn_total")
            with Horizontal(id="budget_cat_txn_buttons"):
                yield Button("Delete", variant="error", id="budget_cat_txn_delete")
            yield Label("Press Escape to close", id="budget_small_label")

    def on_mount(self):
        table = self.query_one("#budget_cat_txn_table", DataTable)
        table.add_columns("Date", "Amount", "Note")
        table.cursor_type = "row"
        self._refresh()

    def _refresh(self):
        table = self.query_one("#budget_cat_txn_table", DataTable)
        table.clear()
        txns = get_budget_transactions(self._budget_id, category_id=self._cat_id)
        total = 0.0
        for t in txns:
            table.add_row(
                t["date"],
                f"${t['amount']:,.2f}",
                t["note"] or "",
                key=str(t["id"]),
            )
            total += t["amount"]

        count = len(txns)
        self.query_one("#budget_cat_txn_total", Label).update(
            f"[bold]Total: ${total:,.2f}[/]  ({count} transaction{'s' if count != 1 else ''})"
        )

    def action_delete_txn(self):
        table = self.query_one("#budget_cat_txn_table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            txn_id = int(row_key)
            txns = get_budget_transactions(self._budget_id, category_id=self._cat_id)
            info = ""
            for t in txns:
                if t["id"] == txn_id:
                    info = f"${t['amount']:,.2f} — {t['category_name']} ({t['date']})"
                    if t["note"]:
                        info += f"\n[dim]{t['note']}[/]"
                    break
            if info:
                self.app.push_screen(
                    BudgetDeleteConfirmModal(info),
                    lambda confirmed: self._on_delete(txn_id, confirmed)
                )
        except (IndexError, ValueError):
            pass

    def _on_delete(self, txn_id, confirmed):
        if confirmed:
            delete_budget_transaction(txn_id)
            self._refresh()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "budget_cat_txn_delete":
            self.action_delete_txn()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)
