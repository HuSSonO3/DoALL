import webbrowser
from datetime import datetime

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Button, Label, Select, DataTable
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.binding import Binding

from .db import (
    init_db, add_job, update_job, delete_job, get_jobs,
    get_distinct_countries, currency_for, STATUSES, TYPES, COUNTRIES,
    auto_ghost_old_applied,
)


# ═══════════════════════════════════════════════════════════════
# Form Modal (Add / Edit)
# ═══════════════════════════════════════════════════════════════

class JobFormModal(ModalScreen):
    """Add or edit a job application entry."""

    def __init__(self, job_data=None):
        super().__init__()
        self._job = job_data  # None = add mode, dict = edit mode
        self._is_edit = job_data is not None

    def compose(self) -> ComposeResult:
        title = "Edit Job" if self._is_edit else "Add Job"
        with VerticalScroll(id="job_form_scroll"):
            yield Label(f"[bold]{title}[/]", id="job_form_title")

            # Row 1: Company + Title
            with Horizontal(classes="job_form_row"):
                with Vertical(classes="job_form_col"):
                    yield Label("Company *")
                    yield Input(placeholder="Company name...", id="job_company")
                with Vertical(classes="job_form_col"):
                    yield Label("Job Title *")
                    yield Input(placeholder="Job title...", id="job_title")

            # Row 2: Salary + Type
            with Horizontal(classes="job_form_row"):
                with Vertical(classes="job_form_col"):
                    yield Label("Salary *")
                    with Horizontal(id="job_salary_row"):
                        yield Input(placeholder="e.g. 120k or 80k-150k", id="job_salary")
                        yield Select(
                            [("Year", "year"), ("Month", "month"), ("Hour", "hour")],
                            value="year", allow_blank=False, id="job_salary_per"
                        )
                with Vertical(classes="job_form_col"):
                    yield Label("Type *")
                    yield Select(
                        [(t, t) for t in TYPES], value="On-site",
                        allow_blank=False, id="job_type"
                    )

            # Row 3: Country + Status
            with Horizontal(classes="job_form_row"):
                with Vertical(classes="job_form_col"):
                    yield Label("Country *")
                    yield Select(
                        [(c, c) for c in COUNTRIES], prompt="Select country...",
                        id="job_country"
                    )
                with Vertical(classes="job_form_col"):
                    yield Label("Status *")
                    yield Select(
                        [(s, s) for s in STATUSES], value="Applied",
                        allow_blank=False, id="job_status"
                    )

            # Row 4: URL + Stage
            with Horizontal(classes="job_form_row"):
                with Vertical(classes="job_form_col"):
                    yield Label("URL *")
                    yield Input(placeholder="https://...", id="job_url")
                with Vertical(classes="job_form_col"):
                    yield Label("Stage")
                    yield Input(placeholder="e.g. Phone screen...", id="job_stage")

            # Row 5: Reason + Remarks
            with Horizontal(classes="job_form_row"):
                with Vertical(classes="job_form_col"):
                    yield Label("Reason")
                    yield Input(placeholder="e.g. Referral...", id="job_reason")
                with Vertical(classes="job_form_col"):
                    yield Label("Remarks")
                    yield Input(placeholder="Any notes...", id="job_remarks")

            with Horizontal(id="job_form_buttons"):
                yield Button("Save", variant="primary", id="job_save")
            yield Label("Press Escape to close", id="job_small_label")

    def on_mount(self):
        if self._is_edit:
            j = self._job
            self.query_one("#job_company", Input).value = j["company_name"]
            self.query_one("#job_title", Input).value = j["job_title"]
            self.query_one("#job_salary", Input).value = str(j["salary"])
            self.call_after_refresh(
                lambda: setattr(self.query_one("#job_salary_per", Select), "value", dict(j).get("salary_per", "year"))
            )
            self.query_one("#job_url", Input).value = j["url"]
            self.query_one("#job_stage", Input).value = j["stage"] or ""
            self.query_one("#job_reason", Input).value = j["reason"] or ""
            self.query_one("#job_remarks", Input).value = j["remarks"] or ""

            # Defer Select.value setting
            self.call_after_refresh(
                lambda: setattr(self.query_one("#job_type", Select), "value", j["type"])
            )
            self.call_after_refresh(
                lambda: setattr(self.query_one("#job_status", Select), "value", j["status"])
            )
            self.call_after_refresh(
                lambda: setattr(self.query_one("#job_country", Select), "value", j["country"])
            )

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "job_save":
            self._try_save()

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(None)

    def _try_save(self):
        company = self.query_one("#job_company", Input).value.strip()
        title = self.query_one("#job_title", Input).value.strip()
        salary = self.query_one("#job_salary", Input).value.strip()
        salary_per = self.query_one("#job_salary_per", Select).value
        jtype = self.query_one("#job_type", Select).value
        status = self.query_one("#job_status", Select).value
        country = self.query_one("#job_country", Select).value
        url = self.query_one("#job_url", Input).value.strip()
        stage = self.query_one("#job_stage", Input).value.strip()
        reason = self.query_one("#job_reason", Input).value.strip()
        remarks = self.query_one("#job_remarks", Input).value.strip()

        # Validate mandatory fields
        if not company:
            self.notify("Company name is required.", severity="error")
            return
        if not title:
            self.notify("Job title is required.", severity="error")
            return
        if not salary:
            self.notify("Salary is required.", severity="error")
            return
        if country == Select.BLANK or country == Select.NULL:
            self.notify("Country is required.", severity="error")
            return
        if not url:
            self.notify("URL is required.", severity="error")
            return
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        self.dismiss({
            "company_name": company, "job_title": title, "salary": salary,
            "salary_per": salary_per, "type": jtype, "status": status,
            "country": country, "url": url,
            "stage": stage, "reason": reason, "remarks": remarks,
        })


# ═══════════════════════════════════════════════════════════════
# Delete Confirm Modal
# ═══════════════════════════════════════════════════════════════

class JobDeleteConfirmModal(ModalScreen):
    def __init__(self, info: str):
        super().__init__()
        self._info = info

    def compose(self) -> ComposeResult:
        with Container(id="job_del_container"):
            yield Label(self._info, id="job_del_label")
            with Horizontal(id="job_del_buttons"):
                yield Button("Delete", variant="error", id="job_del_confirm")
            yield Label("Press Escape to close", id="job_small_label")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "job_del_confirm":
            self.dismiss(True)

    def on_key(self, event):
        if event.key == "escape":
            self.dismiss(False)


# ═══════════════════════════════════════════════════════════════
# Main Widget
# ═══════════════════════════════════════════════════════════════

class JobTrackerWidget(Widget, can_focus=True):

    BINDINGS = [
        Binding("n", "add", "Add Job"),
        Binding("e", "edit", "Edit Job"),
        Binding("d", "delete", "Delete Job"),
        Binding("o", "open_url", "Open URL"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._filter_country = None
        self._filter_status = None
        self._search = ""
        self._search_timer = None

    def compose(self) -> ComposeResult:
        with Vertical(id="job_container"):
            yield Label("[bold]Job Application Tracker[/]", id="job_main_title")

            with Horizontal(id="job_filter_row"):
                yield Input(placeholder="Search company...", id="job_search")
                yield Select(
                    [("All Countries", "")], value="",
                    allow_blank=False, id="job_filter_country"
                )
                yield Select(
                    [("All Statuses", "")], value="",
                    allow_blank=False, id="job_filter_status"
                )

            with Horizontal(id="job_action_row"):
                yield Button("Add Job", variant="primary", id="job_add_btn")
                yield Button("Edit Job", id="job_edit_btn")
                yield Button("Delete Job", variant="error", id="job_del_btn")

            yield Label("", id="job_count_label")
            yield DataTable(id="job_table")

    def on_mount(self):
        init_db()
        auto_ghost_old_applied()

        table = self.query_one("#job_table", DataTable)
        table.add_columns(
            "Company", "Title", "Salary", "Type", "Status",
            "Country", "Stage", "Updated", "URL"
        )
        table.cursor_type = "row"
        table.tooltip = "n: Add  e: Edit  d: Delete  o: Open URL"

        self._refresh_filters()
        self._refresh_table()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "job_add_btn":
            self.action_add()
        elif pid == "job_edit_btn":
            self.action_edit()
        elif pid == "job_del_btn":
            self.action_delete()

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "job_search":
            if self._search_timer:
                self._search_timer.stop()
            self._search_timer = self.set_timer(0.3, self._do_search)

    def _do_search(self):
        self._search = self.query_one("#job_search", Input).value.strip()
        self._refresh_table()

    def on_select_changed(self, event: Select.Changed):
        sid = event.select.id
        if sid == "job_filter_country":
            val = event.select.value
            self._filter_country = val if val else None
            self._refresh_table()
        elif sid == "job_filter_status":
            val = event.select.value
            self._filter_status = val if val else None
            self._refresh_table()

    def action_add(self):
        self._editing_id = None
        self.app.push_screen(JobFormModal(), self._on_save)

    def action_edit(self):
        job = self._get_selected_job()
        if not job:
            return
        self._editing_id = job["id"]
        self.app.push_screen(JobFormModal(job_data=job), self._on_save)

    def action_open_url(self):
        job = self._get_selected_job()
        if not job:
            return
        url = job["url"]
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)

    def action_delete(self):
        job = self._get_selected_job()
        if not job:
            return
        info = f"Delete [bold]{job['job_title']}[/] at {job['company_name']}?"
        self.app.push_screen(
            JobDeleteConfirmModal(info),
            lambda confirmed: self._on_delete(job["id"], confirmed)
        )

    def _on_save(self, data):
        if data is None:
            return
        if getattr(self, "_editing_id", None):
            update_job(self._editing_id, **data)
        else:
            add_job(**data)
        self._editing_id = None
        self._refresh_filters()
        self._refresh_table()

    def _on_delete(self, job_id, confirmed):
        if confirmed:
            delete_job(job_id)
            self._refresh_filters()
            self._refresh_table()

    def _get_selected_job(self):
        table = self.query_one("#job_table", DataTable)
        if table.row_count == 0:
            self.notify("No entries.", severity="error")
            return None
        try:
            row_key = table.ordered_rows[table.cursor_row].key.value
            job_id = int(row_key)
            for j in get_jobs():
                if j["id"] == job_id:
                    return dict(j)
        except (IndexError, ValueError):
            pass
        self.notify("Please select a row first.", severity="error")
        return None

    def _refresh_table(self):
        table = self.query_one("#job_table", DataTable)
        table.clear()
        jobs = get_jobs(country=self._filter_country, status=self._filter_status,
                        search=self._search or None)
        count = len(jobs)
        self.query_one("#job_count_label", Label).update(
            f"[dim]{count} job{'s' if count != 1 else ''}[/]"
        )
        for j in jobs:
            sym = currency_for(j["country"])
            per_map = {"year": "/yr", "month": "/mo", "hour": "/hr"}
            per_suffix = per_map.get(j["salary_per"] if "salary_per" in j.keys() else "year", "")
            table.add_row(
                j["company_name"],
                j["job_title"],
                f"{sym}{j['salary']}{per_suffix}",
                j["type"],
                j["status"],
                j["country"],
                j["stage"] or "—",
                j["updated_at"],
                j["url"][:50],
                key=str(j["id"]),
            )

    def _refresh_filters(self):
        # Country filter
        sel = self.query_one("#job_filter_country", Select)
        current = self._filter_country if self._filter_country else ""
        options = [("All Countries", "")]
        for c in get_distinct_countries():
            options.append((c, c))
        sel.set_options(options)
        sel.value = current

        # Status filter
        sel2 = self.query_one("#job_filter_status", Select)
        current2 = self._filter_status if self._filter_status else ""
        options2 = [("All Statuses", "")]
        for s in STATUSES:
            options2.append((s, s))
        sel2.set_options(options2)
        sel2.value = current2


# ═══════════════════════════════════════════════════════════════
# Tab Wrapper
# ═══════════════════════════════════════════════════════════════

class JobTrackerTab(TabPane):
    def compose(self) -> ComposeResult:
        yield JobTrackerWidget()
