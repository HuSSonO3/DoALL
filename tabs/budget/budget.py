from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Button, Label, Select, DataTable
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding

from .db import (
    init_db, get_or_create_budget, update_total_budget,
    add_budget_category, update_budget_category, get_budget_categories,
    delete_budget_category,
    add_budget_transaction, get_budget_transactions, delete_budget_transaction,
    get_category_summary, get_total_summary,
)
from .modals import (
    BudgetSetTotalModal, BudgetCategoryFormModal, BudgetCategoryEditModal,
    BudgetDeleteConfirmModal, BudgetDeleteCategoryConfirmModal,
    BudgetCategoryTransactionsModal,
)


# ═══════════════════════════════════════════════════════════════
# Main Widget
# ═══════════════════════════════════════════════════════════════

class BudgetWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("n", "add_transaction", "Add Transaction"),
        Binding("d", "delete_transaction", "Delete Transaction"),
        Binding("enter", "view_category_transactions", "View Transactions"),
        Binding("t", "set_total_budget", "Set Total Budget"),
        Binding("c", "add_category", "Add Category"),
        Binding("left", "prev_month", "Previous Month"),
        Binding("right", "next_month", "Next Month"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._budget_id = None
        self._total_budget = 0.0
        self._current_month = datetime.now().strftime("%Y-%m")

    def compose(self) -> ComposeResult:
        with Vertical(id="budget_container"):
            # ── Month navigation ──
            with Horizontal(id="budget_month_nav"):
                yield Button("◀  Prev", id="budget_prev_btn")
                yield Label(self._format_month(self._current_month), id="budget_month_label")
                yield Button("Next  ▶", id="budget_next_btn")

            # ── Set budget button ──
            with Horizontal(id="budget_total_row"):
                yield Button("Set Monthly Budget", variant="primary", id="budget_set_total_btn")
                yield Button("Add Category", id="budget_add_category_btn")

            # ── Summary cards ──
            with Horizontal(id="budget_summary_row"):
                with Vertical(id="budget_card_total"):
                    yield Label("Budget", id="budget_card_total_label")
                    yield Label("RM 0.00", id="budget_card_total_value")
                with Vertical(id="budget_card_spent"):
                    yield Label("Spent", id="budget_card_spent_label")
                    yield Label("RM 0.00", id="budget_card_spent_value")
                with Vertical(id="budget_card_remaining"):
                    yield Label("Remaining", id="budget_card_remaining_label")
                    yield Label("RM 0.00", id="budget_card_remaining_value")

            # ── Transaction input ──
            with Horizontal(id="budget_input_row"):
                yield Input(placeholder="YYYY-MM-DD", id="budget_date")
                yield Input(placeholder="Amount", id="budget_amount")
                yield Select([], prompt="Category", id="budget_category_select")
                yield Input(placeholder="Note (optional)", id="budget_note")
                yield Button("Add", variant="primary", id="budget_add_btn")

            # ── Category progress table ──
            yield Label("Category Progress", id="budget_table_heading")
            yield DataTable(id="budget_table")

            # ── Actions ──
            with Horizontal(id="budget_actions_row"):
                yield Button("View Transactions", variant="primary", id="budget_view_txn_btn")
                yield Button("Edit Category", id="budget_edit_cat_btn")
                yield Button("Delete Category", variant="error", id="budget_delete_category_btn")

    def on_mount(self):
        init_db()

        # Set today's date
        self.query_one("#budget_date", Input).value = datetime.now().strftime("%Y-%m-%d")

        # Setup table
        table = self.query_one("#budget_table", DataTable)
        table.add_columns("Category", "Budget", "Spent", "Remaining", "Progress")
        table.cursor_type = "row"
        table.tooltip = "Enter: View  n: Add  d: Delete  t: Set Budget  c: Add Category  ←/→: Month  ↓:Decrease  ↑:Increase  •:Stagnant"

        self._refresh_all()

    # ── Month navigation ──

    def _format_month(self, month_str):
        dt = datetime.strptime(month_str, "%Y-%m")
        return dt.strftime("%B %Y")

    def _navigate_month(self, delta):
        year, month = map(int, self._current_month.split("-"))
        month += delta
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        self._current_month = f"{year:04d}-{month:02d}"
        self._refresh_all()

    def action_prev_month(self):
        self._navigate_month(-1)

    def action_next_month(self):
        self._navigate_month(1)

    # ── Button dispatch ──

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "budget_add_btn":
            self.action_add_transaction()
        elif pid == "budget_set_total_btn":
            self.action_set_total_budget()
        elif pid == "budget_add_category_btn":
            self.action_add_category()
        elif pid == "budget_view_txn_btn":
            self.action_view_category_transactions()
        elif pid == "budget_edit_cat_btn":
            self.action_edit_category()
        elif pid == "budget_delete_category_btn":
            self.action_delete_category()
        elif pid == "budget_prev_btn":
            self.action_prev_month()
        elif pid == "budget_next_btn":
            self.action_next_month()

    # ── Actions ──

    def action_add_transaction(self):
        date_val = self.query_one("#budget_date", Input).value.strip()
        amount_str = self.query_one("#budget_amount", Input).value.strip()
        cat_val = self.query_one("#budget_category_select", Select).value
        note = self.query_one("#budget_note", Input).value.strip()

        # Check if any categories exist
        cats = get_budget_categories(self._budget_id)
        if not cats:
            self.notify("Add a budget category first.", severity="error")
            return

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

        cat_id = int(cat_val)
        add_budget_transaction(self._budget_id, cat_id, date_val, amount, note)

        # Clear inputs
        self.query_one("#budget_amount", Input).value = ""
        self.query_one("#budget_note", Input).value = ""

        self._refresh_all()

    def action_set_total_budget(self):
        if self._budget_id is None:
            return
        self.app.push_screen(
            BudgetSetTotalModal(self._budget_id, self._total_budget),
            self._on_total_budget_set
        )

    def _on_total_budget_set(self, amount):
        if amount is not None:
            update_total_budget(self._budget_id, amount)
            self._refresh_all()

    def action_add_category(self):
        if self._budget_id is None:
            return
        self.app.push_screen(
            BudgetCategoryFormModal(self._budget_id),
            self._on_category_added
        )

    def _on_category_added(self, data):
        if data is not None:
            add_budget_category(self._budget_id, data["name"], data["amount"], data["impact"])
            self._refresh_all()

    def action_edit_category(self):
        if self._budget_id is None:
            return
        table = self.query_one("#budget_table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            cat_id = int(row_key)
            cats = get_budget_categories(self._budget_id)
            cat = None
            for c in cats:
                if c["id"] == cat_id:
                    cat = c
                    break
            if cat:
                # Get spent for this category
                summary = get_category_summary(self._budget_id)
                spent = 0.0
                for s in summary:
                    if s["id"] == cat_id:
                        spent = s["spent"]
                        break
                self.app.push_screen(
                    BudgetCategoryEditModal(self._budget_id, dict(cat), spent),
                    lambda result: self._on_category_edited(cat_id, result)
                )
        except (IndexError, ValueError):
            pass

    def _on_category_edited(self, cat_id, result):
        if result is None:
            return
        cats = get_budget_categories(self._budget_id)
        cat = None
        for c in cats:
            if c["id"] == cat_id:
                cat = c
                break
        if not cat:
            return

        new_name = result["name"]
        new_impact = result["impact"]
        old_impact = cat["budget_impact"]

        # Use budget_amount if set, otherwise spent (for increase/stagnant which have 0 budget)
        amount = cat["budget_amount"]
        if amount <= 0:
            amount = self._get_category_spent(cat_id)

        # Update the category
        update_budget_category(cat_id, self._budget_id, new_name, cat["budget_amount"], new_impact)

        # Recalculate total budget: only "increase" changes the total
        new_total = self._total_budget
        if old_impact == "increase":
            new_total -= amount
        if new_impact == "increase":
            new_total += amount

        update_total_budget(self._budget_id, new_total)
        self._refresh_all()

    def _get_category_spent(self, cat_id):
        for s in get_category_summary(self._budget_id):
            if s["id"] == cat_id:
                return s["spent"]
        return 0.0

    def action_delete_category(self):
        if self._budget_id is None:
            return
        table = self.query_one("#budget_table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            cat_id = int(row_key)
            cats = get_budget_categories(self._budget_id)
            cat_name = ""
            for c in cats:
                if c["id"] == cat_id:
                    cat_name = c["name"]
                    break
            if cat_name:
                txns = get_budget_transactions(self._budget_id, category_id=cat_id)
                self.app.push_screen(
                    BudgetDeleteCategoryConfirmModal(cat_name, len(txns)),
                    lambda confirmed: self._on_category_deleted(cat_id, confirmed)
                )
        except (IndexError, ValueError):
            pass

    def _on_category_deleted(self, cat_id, confirmed):
        if confirmed:
            delete_budget_category(cat_id, self._budget_id)
            self._refresh_all()

    def action_view_category_transactions(self):
        """Open a modal showing all transactions for the selected category."""
        table = self.query_one("#budget_table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            cat_id = int(row_key)
            cats = get_budget_categories(self._budget_id)
            cat_name = ""
            for c in cats:
                if c["id"] == cat_id:
                    cat_name = c["name"]
                    break
            if cat_name:
                self.app.push_screen(
                    BudgetCategoryTransactionsModal(
                        self._budget_id, cat_id, cat_name,
                        self._format_month(self._current_month)
                    ),
                    self._on_category_view_closed
                )
        except (IndexError, ValueError):
            pass

    def _on_category_view_closed(self, _data):
        self._refresh_all()

    def action_delete_transaction(self):
        table = self.query_one("#budget_table", DataTable)
        if table.row_count == 0:
            return
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            cat_id = int(row_key)
            txns = get_budget_transactions(self._budget_id, category_id=cat_id)
            if not txns:
                self.notify("No transactions in this category.", severity="error")
                return

            latest = txns[0]
            info = f"RM {latest['amount']:,.2f} — {latest['category_name']} ({latest['date']})\n"
            if len(txns) > 1:
                info += f"[dim]({len(txns)} total transactions in this category)[/]"
            self.app.push_screen(
                BudgetDeleteConfirmModal(info),
                lambda confirmed: self._on_txn_deleted(latest["id"], confirmed)
            )
        except (IndexError, ValueError):
            pass

    def _on_txn_deleted(self, txn_id, confirmed):
        if confirmed:
            delete_budget_transaction(txn_id)
            self._refresh_all()

    # ── Refresh helpers ──

    def _refresh_all(self):
        self._ensure_budget()
        self._refresh_month_label()
        self._refresh_summary()
        self._refresh_table()
        self._refresh_category_select()

    def _ensure_budget(self):
        self._budget_id, self._total_budget = get_or_create_budget(self._current_month)

    def _refresh_month_label(self):
        self.query_one("#budget_month_label", Label).update(
            f"[bold]{self._format_month(self._current_month)}[/]"
        )

    def _refresh_summary(self):
        s = get_total_summary(self._budget_id)
        self.query_one("#budget_card_total_value", Label).update(f"RM {s['total_budget']:,.2f}")
        self.query_one("#budget_card_spent_value", Label).update(f"RM {s['total_spent']:,.2f}")

        remaining_label = self.query_one("#budget_card_remaining_value", Label)
        remaining_label.update(f"RM {s['total_remaining']:,.2f}")
        if s["total_remaining"] < 0:
            remaining_label.add_class("negative")
        else:
            remaining_label.remove_class("negative")

    def _refresh_table(self):
        table = self.query_one("#budget_table", DataTable)
        table.clear()
        categories = get_category_summary(self._budget_id)
        impact_labels = {"decrease": "↓", "increase": "↑", "stagnant": "•"}
        for cat in categories:
            impact = impact_labels.get(cat["budget_impact"], "•")

            if cat["budget_impact"] == "decrease" and cat["budget_amount"] > 0:
                pct = int((cat["spent"] / cat["budget_amount"]) * 100)
                progress = f"RM {cat['spent']:,.2f} / RM {cat['budget_amount']:,.2f} ({pct}%)"
                budget_str = f"RM {cat['budget_amount']:,.2f}"
                spent_str = f"RM {cat['spent']:,.2f}"
                remaining_str = f"RM {cat['remaining']:,.2f}"
            else:
                progress = f"RM {cat['spent']:,.2f} tracked"
                budget_str = "—"
                spent_str = f"RM {cat['spent']:,.2f}"
                remaining_str = "—"

            table.add_row(
                f"{impact} {cat['name']}",
                budget_str,
                spent_str,
                remaining_str,
                progress,
                key=str(cat["id"]),
            )

    def _refresh_category_select(self):
        sel = self.query_one("#budget_category_select", Select)
        cats = get_budget_categories(self._budget_id)
        options = [(c["name"], str(c["id"])) for c in cats]
        sel.set_options(options)


# ═══════════════════════════════════════════════════════════════
# Tab Wrapper
# ═══════════════════════════════════════════════════════════════

class BudgetTab(TabPane):
    def compose(self) -> ComposeResult:
        yield BudgetWidget()
