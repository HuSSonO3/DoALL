import socket

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Label, DataTable, Button
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical


COMMON_PORTS = [
    20, 21, 22, 25, 53, 80, 110, 143, 443, 465,
    587, 993, 995, 1433, 3000, 3306, 4000, 5000,
    5432, 6379, 8000, 8080, 8443, 9000, 27017,
]

TIMEOUT = 0.15


def service_name(port: int) -> str:
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return "—"


def check_port(port: int) -> tuple[int, str, str]:
    """Return (port, status_label, service_name)."""
    if port < 0 or port > 65535:
        return (port, "[bold red]Invalid[/]", "—")
    svc = service_name(port)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    try:
        result = s.connect_ex(("127.0.0.1", port))
        if result == 0:
            return (port, "[bold green]OPEN[/]", svc)
        else:
            return (port, "[dim]Closed[/]", svc)
    except Exception:
        return (port, "[bold red]Error[/]", svc)
    finally:
        s.close()


class PortCheckerWidget(Widget, can_focus=True):

    def compose(self) -> ComposeResult:
        with Vertical(id="port_container"):
            yield Label("[bold]Port Checker[/]", id="port_title")

            with Horizontal(id="port_input_row"):
                yield Input(
                    placeholder="Port or range (e.g. 3000 or 8000-8010)",
                    id="port_input",
                )

            with Horizontal(id="port_action_row"):
                yield Button("Scan Common Ports", variant="primary", id="port_scan_common_btn")
                yield Button("Scan Range", id="port_scan_range_btn")

            yield Label("", id="port_status")

            yield DataTable(id="port_results")

    def on_mount(self):
        self.query_one("#port_input", Input).focus()
        table = self.query_one("#port_results", DataTable)
        table.add_columns("Port", "Status", "Service")
        table.cursor_type = "row"
        self._check_timer = None

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "port_input":
            if self._check_timer:
                self._check_timer.stop()
            self._check_timer = self.set_timer(0.3, self._on_input)

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "port_input":
            self._scan_range()

    def on_button_pressed(self, event: Button.Pressed):
        pid = event.button.id
        if pid == "port_scan_common_btn":
            self._scan(COMMON_PORTS)
        elif pid == "port_scan_range_btn":
            self._scan_range()

    # ── actions ──────────────────────────────────────────────

    def _on_input(self):
        """Debounced single-port check from the input field."""
        text = self.query_one("#port_input", Input).value.strip()
        if not text or not text.isdigit():
            self.query_one("#port_status", Label).update("")
            return
        port = int(text)
        if port < 1 or port > 65535:
            self.query_one("#port_status", Label).update(
                "[bold red]Invalid port — must be 1–65535[/]"
            )
            return
        self._scan([port])

    def _scan_range(self):
        """Parse the input as a single port or range and scan."""
        text = self.query_one("#port_input", Input).value.strip()
        status = self.query_one("#port_status", Label)

        if not text:
            status.update("")
            return

        # Try single port
        if text.isdigit():
            port = int(text)
            if port < 1 or port > 65535:
                status.update("[bold red]Invalid port — must be 1–65535[/]")
                return
            self._scan([port])
            return

        # Try range: "X-Y" or "X - Y"
        import re
        m = re.match(r"(\d+)\s*-\s*(\d+)", text)
        if not m:
            status.update("[bold red]Invalid — use a port number or range like 8000-8010[/]")
            return

        start, end = int(m.group(1)), int(m.group(2))
        for p in (start, end):
            if p < 1 or p > 65535:
                status.update("[bold red]Port out of range — must be 1–65535[/]")
                return

        if start > end:
            start, end = end, start

        ports = list(range(start, end + 1))
        if len(ports) > 500:
            status.update(
                f"[bold yellow]Large range ({len(ports)} ports) — scanning, this may be slow…[/]"
            )
        self._scan(ports)

    def _scan(self, ports: list[int]):
        table = self.query_one("#port_results", DataTable)
        table.clear()
        status = self.query_one("#port_status", Label)

        if not ports:
            return

        open_count = 0
        for port in ports:
            p, state, svc = check_port(port)
            table.add_row(str(p), state, svc)
            if "OPEN" in state:
                open_count += 1

        # Scroll back to top
        if table.row_count > 0:
            table.cursor_coordinate = (0, 0)

        total = len(ports)
        status.update(
            f"[dim]{total} port{'s' if total != 1 else ''} checked, "
            f"{open_count} [bold green]open[/][/]"
        )


class PortCheckerTab(TabPane):
    def compose(self) -> ComposeResult:
        yield PortCheckerWidget()
