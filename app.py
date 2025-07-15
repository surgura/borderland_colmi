from __future__ import annotations

from nicegui import ui, app

import nicegui
from client import Client
from datetime import datetime, timedelta
from filter_abs import FilterAbs
import asyncio
from accelerometer_data import AccelerometerData
from rtmidi import MidiOut
from typing import Callable
from enum import Enum, auto
from scan_for_rings import scan_for_rings
import json
from pathlib import Path


async def filter_abs_task(filter_abs: FilterAbs, plot, midi: MidiOut) -> None:
    async for abs_output in filter_abs.run():
        plot.push([abs_output.timestamp], [[abs_output.value]], y_limits=(0, 3000))
        print("send!")
        midi.send_message(
            [176, 1, round((min(2500, max(0, abs_output.value - 500))) / 2500 * 127)]
        )


class RingStatus(Enum):
    CONNECTED = auto()
    DISCONNECTED = auto()
    CONNECTING = auto()


class RingManager:
    _address: str
    _name: str
    _on_connect: Callable[[], None]
    _on_disconnect: Callable[[], None]
    _on_connecting: Callable[[], None]

    _ring_status: RingStatus

    def __init__(
        self,
        address: str,
        name: str,
        on_connect: Callable[[], None],
        on_disconnect: Callable[[], None],
        on_connecting: Callable[[], None],
    ) -> None:
        self._address = address
        self._name = name
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_connecting = on_connecting

        self._ring_status = RingStatus.DISCONNECTED

    @property
    def address(self) -> str:
        return self._address

    @property
    def name(self) -> str:
        return self._name

    async def run(self) -> None:
        while True:
            await asyncio.sleep(1)
            self._ring_status = RingStatus.CONNECTING
            self._on_connecting()
            await asyncio.sleep(1)
            self._ring_status = RingStatus.CONNECTED
            self._on_connect()
            await asyncio.sleep(1)
            self._ring_status = RingStatus.DISCONNECTED
            self._on_disconnect()

    @property
    def status(self) -> RingStatus:
        return self._ring_status


class UIApp:
    _ring_managers: dict[str, RingManager]

    _rings: UIRings
    _midi: UIMidi
    _signals: UISignals

    _tab_rings: nicegui.elements.tabs.Tab

    def __init__(self) -> None:
        with ui.tabs() as tabs:
            self._ring_managers = {}

            self._tab_rings = ui.tab("Rings", icon="question_mark")
            tab_midi = ui.tab("MIDI output", icon="warning")
            tab_signals = ui.tab("Signals", icon="")

        with ui.tab_panels(tabs, value=self._tab_rings).classes("w-full"):
            with ui.tab_panel(self._tab_rings):
                self._rings = UIRings(on_add_ring=self._on_add_ring)
            with ui.tab_panel(tab_midi):
                self._midi = UIMidi()
            with ui.tab_panel(tab_signals):
                self._signals = UISignals()

    async def startup(self) -> None:
        path = Path("rings.json")
        if path.is_file():
            with open(path, "r") as f:
                rings = json.load(f)
                for ring in rings:
                    self._rings.add(address=ring["address"], name=ring["name"])

    def _on_add_ring(self, address: str, name: str) -> str | None:
        """
        Add a new ring.

        None is successful. str is error message.
        """
        if address == "":
            return "Address cannot be empty."
        elif address in self._ring_managers.keys():
            return f"Address {address} already added."
        else:
            self._ring_managers[address] = RingManager(
                address=address,
                name=name,
                on_connect=lambda: self._on_ring_connect(address),
                on_disconnect=lambda: self._on_ring_disconnect(address),
                on_connecting=lambda: self._on_ring_connecting(address),
            )
            asyncio.create_task(self._ring_managers[address].run())

        rings = [
            {"address": r.address, "name": r.name} for r in self._ring_managers.values()
        ]
        with open("rings.json", "w") as f:
            json.dump(rings, f)

    def _on_ring_connect(self, address: str) -> None:
        self._update_rings_icon()
        self._rings.on_ring_connect(address)

    def _on_ring_disconnect(self, address: str) -> None:
        self._update_rings_icon()
        self._rings.on_ring_disconnect(address)

    def _on_ring_connecting(self, address: str) -> None:
        self._update_rings_icon()
        self._rings.on_ring_connecting(address)

    def _update_rings_icon(self) -> None:
        if any(
            [r.status == RingStatus.DISCONNECTED for r in self._ring_managers.values()]
        ):
            self._tab_rings.icon = "warning"
        elif any(
            [r.status == RingStatus.CONNECTING for r in self._ring_managers.values()]
        ):
            self._tab_rings.icon = "bluetooth_searching"
        else:
            self._tab_rings.icon = "check"


class UIRings:
    _on_add_ring: Callable[[str, str], bool]

    _tabs = nicegui.elements.tabs.Tabs
    _panels = nicegui.elements.tabs.TabPanels
    _scan_list = nicegui.elements.list.List
    _tab_new = nicegui.elements.tabs.Tab
    _ring_address = nicegui.elements.input.Input

    _ring_tabs: dict[str, IORingTab] = {}
    _ring_tabs_ui: dict[str, nicegui.elements.tabs.Tab] = {}

    _scanning: bool

    def __init__(self, on_add_ring: Callable[[str, str], str | None]) -> None:
        """
        on_add_ring is None if successful, str is error message.
        """
        self._on_add_ring = on_add_ring

        self._scanning = False

        with ui.splitter(value=None).classes("w-full") as splitter:
            with splitter.before:
                with ui.tabs().props("vertical").classes("w-full") as tabs:
                    self._tabs = tabs
                    self._tab_new = ui.tab("Add", icon="add")
            with splitter.after:
                with (
                    ui.tab_panels(tabs, value=self._tab_new)
                    .props("vertical")
                    .classes("w-full h-full")
                ) as panels:
                    self._panels = panels
                    with ui.tab_panel(self._tab_new):
                        self._ring_address = ui.input(label="Ring address")
                        ui.button(
                            text="Add",
                            on_click=lambda: self.add(
                                address=self._ring_address.value,
                                name=self._ring_address.value,
                            ),
                        )

                        ui.separator()

                        ui.button(text="Scan for rings", on_click=self._scan)
                        with ui.list().props("dense separator") as scan_list:
                            self._scan_list = scan_list

    def add(self, address: str, name: str) -> None:
        result = self._on_add_ring(address, name)
        if result is None:
            with self._tabs:
                self._ring_tabs_ui[address] = ui.tab(name, icon="question_mark")
                self._tab_new.move(target_index=-1)
            with self._panels:
                with ui.tab_panel(name):
                    self._ring_tabs[address] = IORingTab(
                        address=address, name=name, on_remove=self._on_ring_tab_remove
                    )
        else:
            ui.notify(message=result, type="warning")

    def on_ring_connect(self, address: str) -> None:
        self._ring_tabs_ui[address].icon = "check"
        self._ring_tabs[address].on_connect()

    def on_ring_disconnect(self, address: str) -> None:
        self._ring_tabs_ui[address].icon = "warning"
        self._ring_tabs[address].on_disconnect()

    def on_ring_connecting(self, address: str) -> None:
        self._ring_tabs_ui[address].icon = "bluetooth_searching"
        self._ring_tabs[address].on_connecting()

    async def _scan(self) -> None:
        if not self._scanning:
            self._scanning = True
            with self._scan_list:
                self._scan_list.clear()
                ui.spinner("dots", size="lg", color="red")
            ring_devices = await scan_for_rings()
            with self._scan_list:
                self._scan_list.clear()
                table = ui.table(
                    columns=[
                        {
                            "name": "Name",
                            "label": "Name",
                            "field": "Name",
                            "required": True,
                            "align": "left",
                        },
                        {
                            "name": "Address",
                            "label": "Address",
                            "field": "Address",
                            "required": True,
                            "align": "left",
                        },
                    ],
                    rows=[
                        {
                            "Name": f"{ring.name}",
                            "Address": f"{ring.address}",
                        }
                        for ring in ring_devices
                    ],
                )

                # I don't get this part yet but I copied it from the docs and it works.
                # Adds the + to the table rows
                table.add_slot(
                    "header",
                    r"""
                    <q-tr :props="props">
                        <q-th auto-width />
                        <q-th v-for="col in props.cols" :key="col.name" :props="props">
                            {{ col.label }}
                        </q-th>
                    </q-tr>
                """,
                )
                table.add_slot(
                    "body",
                    r"""
                    <q-tr :props="props">
                        <q-td auto-width>
                            <q-btn size="sm" color="accent" round dense
                                @click="$parent.$emit('add', props.row.Address, props.row.Name)"
                                icon=add />
                        </q-td>
                        <q-td v-for="col in props.cols" :key="col.name" :props="props">
                            {{ col.value }}
                        </q-td>
                    </q-tr>
                """,
                )
                table.on("add", lambda msg: self.add(msg.args[0], msg.args[1]))
            self._scanning = False

    def _on_ring_tab_remove(self, address: str) -> None:
        ui.notify(message="TODO")

    def remove_tab(self):
        self.tabs.remove(0)
        self.panels.remove(0)


class IORingTab:
    _on_remove: Callable[[str], None]

    _status: nicegui.elements.item.ItemLabel

    def __init__(
        self, address: str, name: str, on_remove: Callable[[str], None]
    ) -> None:
        self._on_remove = on_remove

        with ui.list().props("separator"):
            with ui.item():
                with ui.item_section():
                    ui.label("Name:").classes("text-bold")
                with ui.item_section():
                    ui.item_label(f"{name}")
            with ui.item():
                with ui.item_section():
                    ui.label("Address:").classes("text-bold")
                with ui.item_section():
                    ui.item_label(f"{address}")
            with ui.item():
                with ui.item_section():
                    ui.label("Status:").classes("text-bold")
                with ui.item_section():
                    self._status = ui.item_label("?")
        ui.button(text="Remove", on_click=self._on_remove)

    def on_connect(self) -> None:
        self._status.text = "Connected"

    def on_disconnect(self) -> None:
        self._status.text = "Disconnected"

    def on_connecting(self) -> None:
        self._status.text = "Connecting"


class UIMidi:
    def __init__(self) -> None:
        pass


class UISignals:
    def __init__(self) -> None:
        pass


def run_app(addresses: list[str]) -> None:
    filter_abs = FilterAbs(
        update_period=timedelta(milliseconds=100),
        window_size=timedelta(milliseconds=1000),
    )

    midiout = MidiOut()

    if len(addresses) == 0:
        raise ValueError("Must have at least one address to connect to.")
    print(f"Running with addresses:\n{'\n'.join(addresses)}")

    async def on_enable_accelerometer():
        await client.enable_raw_sensor_data()

    async def on_disable_accelerometer():
        await client.disable_raw_sensor_data()

    async def on_raw_sensor_data(acc_x: int, acc_y: int, acc_z: int):
        now = datetime.now()
        accelerometer_data = AccelerometerData(x=acc_x, y=acc_y, z=acc_z, timestamp=now)
        filter_abs.on_accelerometer_data(accelerometer_data)
        # line_plot.push([now], [[acc_x], [acc_y], [acc_z]], y_limits=(-5000, 5000))

    client = Client(address=addresses[0], on_raw_sensor_data=on_raw_sensor_data)

    ui.dark_mode(None)

    # ui.button("Enable accelerometer", on_click=on_enable_accelerometer)
    # ui.button("Disable accelerometer", on_click=on_disable_accelerometer)

    # line_plot = ui.line_plot(
    #     n=3, limit=100, figsize=(10, 4), update_every=20, layout="constrained"
    # ).with_legend(["x", "y", "z"])

    # line_plot2 = ui.line_plot(
    #     n=1, limit=100, figsize=(10, 4), update_every=1, layout="constrained"
    # ).with_legend(["abs"])

    ui_app = UIApp()

    @app.on_startup
    async def startup(self) -> None:
        await ui_app.startup()

    # @app.on_startup
    # async def startup():
    # pass
    # await client.__aenter__()
    # midiout.open_virtual_port("My midi thing")
    # asyncio.create_task(filter_abs_task(filter_abs, line_plot2, midiout))

    # @app.on_shutdown
    # async def shutdown():
    #     await client.__aexit__(None, None, None)

    ui.run()
