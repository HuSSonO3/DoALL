import ipaddress

from textual.app import ComposeResult
from textual.widgets import TabPane, Input, Label, DataTable
from textual.widget import Widget
from textual.containers import Container, Horizontal, Vertical
from textual.binding import Binding


class SubnetCalcWidget(Widget, can_focus=True):

    def compose(self) -> ComposeResult:
        with Container(id="sub_container"):
            yield Label("[bold]IP Subnet Calculator[/]", id="sub_title")

            with Horizontal(id="sub_input_row"):
                yield Input(
                    placeholder="e.g. 192.168.1.0/24 or 10.0.0.1/255.255.255.0",
                    id="sub_input"
                )
            yield Label("", id="sub_status")

            yield DataTable(id="sub_results")

    def on_mount(self):
        self.query_one("#sub_input", Input).focus()
        table = self.query_one("#sub_results", DataTable)
        table.add_columns("Field", "Value")
        table.cursor_type = "row"
        self._calc_timer = None

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "sub_input":
            if self._calc_timer:
                self._calc_timer.stop()
            self._calc_timer = self.set_timer(0.3, self._calc)

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "sub_input":
            self._calc()

    def _calc(self):
        text = self.query_one("#sub_input", Input).value.strip()
        status = self.query_one("#sub_status", Label)
        table = self.query_one("#sub_results", DataTable)
        table.clear()

        if not text:
            status.update("")
            return

        # Try IPv4 or IPv6
        network = None
        try:
            network = ipaddress.IPv4Network(text, strict=False)
            family = "IPv4"
        except Exception:
            try:
                network = ipaddress.IPv6Network(text, strict=False)
                family = "IPv6"
            except Exception:
                status.update("[bold red]Invalid IP/CIDR[/]")
                return

        status.update(f"[dim]{family}  /{network.prefixlen}[/]")

        def add(k, v):
            table.add_row(k, str(v))

        add("Address", network.network_address)
        add("Network", f"{network.network_address}/{network.prefixlen}")
        add("Netmask", network.netmask)
        if family == "IPv4":
            add("Wildcard Mask", network.hostmask)
        add("Broadcast", network.broadcast_address if family == "IPv4" else "N/A (IPv6)")

        add("Total Addresses", f"{network.num_addresses:,}")

        total = network.num_addresses
        if total <= 5000:
            hosts = list(network.hosts())
            if hosts:
                add("Host Range", f"{hosts[0]}  —  {hosts[-1]}")
        else:
            add("Host Range", f"[dim]{total:,} addresses, too many to enumerate[/]")

        add("Prefix Length", f"/{network.prefixlen}")
        add("Is Private", "Yes" if network.is_private else "No")
        add("Is Global", "Yes" if network.is_global else "No")
        if family == "IPv4":
            add("Is Loopback", "Yes" if network.is_loopback else "No")
            add("Is Link-Local", "Yes" if network.is_link_local else "No")
            add("Is Multicast", "Yes" if network.is_multicast else "No")


class SubnetCalcTab(TabPane):
    def compose(self) -> ComposeResult:
        yield SubnetCalcWidget()
