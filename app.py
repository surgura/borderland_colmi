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


async def filter_abs_task(filter_abs: FilterAbs, plot, midi: MidiOut) -> None:
    async for abs_output in filter_abs.run():
        plot.push([abs_output.timestamp], [[abs_output.value]], y_limits=(0, 3000))
        print("send!")
        midi.send_message(
            [176, 1, round((min(2500, max(0, abs_output.value - 500))) / 2500 * 127)]
        )


class RingManager:
    _address: str

    def __init__(self, address: str) -> None:
        self._address = address

    @property
    def address(self) -> str:
        return self._address


class UIApp:
    _ring_managers: dict[str, RingManager]

    _rings: UIRings
    _midi: UIMidi
    _signals: UISignals

    def __init__(self) -> None:
        with ui.tabs() as tabs:
            self._ring_managers = {}

            tab_rings = ui.tab("Rings", icon="check")
            tab_midi = ui.tab("MIDI output", icon="warning")
            tab_signals = ui.tab("Signals", icon="")

        with ui.tab_panels(tabs, value=tab_rings).classes("w-full"):
            with ui.tab_panel(tab_rings):
                self._rings = UIRings(on_add_ring=self._on_add_ring)
            with ui.tab_panel(tab_midi):
                self._midi = UIMidi()
            with ui.tab_panel(tab_signals):
                self._signals = UISignals()

    def _on_add_ring(self, address: str) -> str | None:
        """
        Add a new ring.

        None is successful. str is error message.
        """
        if address == "":
            return "Address cannot be empty."
        elif address in self._ring_managers.keys():
            return f"Address {address} already added."
        else:
            self._ring_managers[address] = RingManager(address=address)


class UIRings:
    _on_add_ring: Callable[[str], bool]

    _tabs = nicegui.elements.tabs.Tabs
    _panels = nicegui.elements.tabs.TabPanels
    _scan_list = nicegui.elements.list.List
    _tab_new = nicegui.elements.tabs.Tab
    _ring_address = nicegui.elements.input.Input

    def __init__(self, on_add_ring: Callable[[str], str | None]) -> None:
        """
        on_add_ring is None if successful, str is error message.
        """
        self._on_add_ring = on_add_ring

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
                        ui.button(text="Add", on_click=self._add)

                        ui.separator()

                        ui.button(text="Scan for rings", on_click=self._scan)
                        with ui.list().props("dense separator") as scan_list:
                            self._scan_list = scan_list

    def _add(self) -> None:
        result = self._on_add_ring(self._ring_address.value)
        if result is None:
            with self._tabs:
                ui.tab(self._ring_address.value, icon="bluetooth_searching")  # warning
                self._tab_new.move(target_index=-1)
            with self._panels:
                with ui.tab_panel(self._ring_address.value):
                    ui.label(self._ring_address.value)

        else:
            ui.notify(message=result, type="warning")

    def _scan(self) -> None:
        with self._scan_list:
            self._scan_list.clear()
            ui.item("TODO")

    def remove_tab(self):
        self.tabs.remove(0)
        self.panels.remove(0)


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
    async def startup():
        pass
        # await client.__aenter__()
        # midiout.open_virtual_port("My midi thing")
        # asyncio.create_task(filter_abs_task(filter_abs, line_plot2, midiout))

    @app.on_shutdown
    async def shutdown():
        await client.__aexit__(None, None, None)

    ui.run()
