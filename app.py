from __future__ import annotations

from nicegui import ui

import nicegui
import asyncio
from accelerometer_data import AccelerometerData
from typing import Callable
from scan_for_rings import scan_for_rings
import json
from pathlib import Path
from ring_manager import RingManager, RingStatus
from filters import Filters
from midi_out import MidiOut
from filter_abs import FilterAbsOutput
from ui_midi import UIMidi
from dataclasses import asdict, fields
from midi_config import MidiConfig


class App:
    _ring_managers: dict[str, RingManager]
    _ring_manager_tasks: dict[str, asyncio.Task]

    _rings: UIRings
    _midi: UIMidi
    _signals: UISignals

    _tab_rings: nicegui.elements.tabs.Tab
    _tab_midi: nicegui.elements.tabs.Tab

    _client: nicegui.context.Context.client

    _filters: Filters
    _filters_task: asyncio.Task | None

    _midi_out: MidiOut

    _midi_config: MidiConfig

    def __init__(self) -> None:
        ui.dark_mode(None)

        self._load_midi_config()

        with ui.tabs() as tabs:
            self._client = ui.context.client

            self._ring_managers = {}
            self._ring_manager_tasks = {}

            self._tab_rings = ui.tab("Rings", icon="question_mark")
            self._tab_midi = ui.tab("MIDI", icon="warning")
            tab_signals = ui.tab("Signals", icon="")

        with ui.tab_panels(tabs, value=self._tab_rings).classes("w-full"):
            with ui.tab_panel(self._tab_rings):
                self._rings = UIRings(on_add_ring=self._on_add_ring)
            with ui.tab_panel(self._tab_midi):
                self._midi = UIMidi(
                    self._midi_config,
                    self._on_midi_ring_1_address,
                    self._on_midi_ring_2_address,
                    self._on_midi_ring_3_address,
                )
            with ui.tab_panel(tab_signals):
                self._signals = UISignals()

        self._filters = Filters(on_abs_filter_output=self._on_abs_filter_output)
        self._midi_out = MidiOut()

    async def startup(self) -> None:
        self._midi_out.open()
        self._update_midi_icon()
        self._filters_task = asyncio.create_task(self._filters.run())

        path = Path("rings.json")
        if path.is_file():
            with open(path, "r") as f:
                rings = json.load(f)
                for ring in rings:
                    self._rings.add(address=ring["address"], name=ring["name"])

    async def shutdown(self) -> None:
        self._midi_out.close()
        print("Shutting down ring communication..")
        for ring in self._ring_managers.values():
            await ring.close()
        print("Done")
        self._filters.close()
        print("Waiting background tasks to finish..")
        await asyncio.gather(*self._ring_manager_tasks.values(), self._filters_task)
        print("Done.")

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
                on_connect_fail=lambda msg: self._on_ring_connect_fail(address, msg),
                on_raw_sensor_data=lambda data: self._on_ring_raw_sensor_data(
                    address, data
                ),
            )
            self._ring_manager_tasks[address] = asyncio.create_task(
                self._ring_managers[address].run()
            )
            self._filters.on_ring_add(address=address)
            self._midi.update_ring_addresses(addresses=list(self._ring_managers.keys()))

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

    def _on_ring_connect_fail(self, address: str, msg: str) -> None:
        self._update_rings_icon()
        self._rings.on_ring_connect_fail(address)
        with self._client:
            ui.notify(message=f"{address}: {msg}", type="negative")

    async def _on_ring_raw_sensor_data(
        self, address: str, data: AccelerometerData
    ) -> None:
        self._filters.on_raw_sensor_data(address, data)

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

    def _update_midi_icon(self) -> None:
        if any(
            getattr(self._midi_config, f.name) is None
            for f in fields(self._midi_config)
        ):
            self._tab_midi.icon = "warning"
        else:
            self._tab_midi.icon = "check"

    def _on_abs_filter_output(self, address: str, output: FilterAbsOutput) -> None:
        if (
            self._midi_config.abs_ring_1 is not None
            and address == self._midi_config.abs_ring_1
        ):
            self._midi_out.send_abs_1(max(0.0, min(1.0, (output.value - 500) / 2500)))
        if (
            self._midi_config.abs_ring_2 is not None
            and address == self._midi_config.abs_ring_2
        ):
            self._midi_out.send_abs_2(max(0.0, min(1.0, (output.value - 500) / 2500)))
        if (
            self._midi_config.abs_ring_3 is not None
            and address == self._midi_config.abs_ring_3
        ):
            self._midi_out.send_abs_3(max(0.0, min(1.0, (output.value - 500) / 2500)))

    def _on_midi_ring_1_address(self, address: str) -> None:
        self._midi_config.abs_ring_1 = address
        self._save_midi_config()
        self._update_midi_icon()

    def _on_midi_ring_2_address(self, address: str) -> None:
        self._midi_config.abs_ring_2 = address
        self._save_midi_config()
        self._update_midi_icon()

    def _on_midi_ring_3_address(self, address: str) -> None:
        self._midi_config.abs_ring_3 = address
        self._save_midi_config()
        self._update_midi_icon()

    def _save_midi_config(self) -> None:
        with open("midi.json", "w") as f:
            json.dump(asdict(self._midi_config), f)

    def _load_midi_config(self) -> None:
        path = Path("midi.json")
        if path.is_file():
            with open(path, "r") as f:
                self._midi_config = MidiConfig(**json.load(f))
        else:
            self._midi_config = MidiConfig()


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

    def on_ring_connect_fail(self, address: str) -> None:
        self._ring_tabs_ui[address].icon = "warning"
        self._ring_tabs[address].on_connect_fail()

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

    def on_connect_fail(self) -> None:
        self._status.text = "Disconnected"


class UISignals:
    def __init__(self) -> None:
        pass
