from nicegui import ui
import nicegui
from typing import Callable
from midi_config import MidiConfig


class UIMidi:
    _on_ring_1_address: Callable[[str], None]
    _on_ring_2_address: Callable[[str], None]
    _on_ring_3_address: Callable[[str], None]

    _ring_1_address: nicegui.elements.select.Select
    _ring_2_address: nicegui.elements.select.Select
    _ring_3_address: nicegui.elements.select.Select

    _ring_1_address_label: nicegui.elements.label.Label
    _ring_2_address_label: nicegui.elements.label.Label
    _ring_3_address_label: nicegui.elements.label.Label

    def __init__(
        self,
        midi_config: MidiConfig,
        on_ring_1_address: Callable[[str], None],
        on_ring_2_address: Callable[[str], None],
        on_ring_3_address: Callable[[str], None],
    ) -> None:
        self._on_ring_1_address = on_ring_1_address
        self._on_ring_2_address = on_ring_2_address
        self._on_ring_3_address = on_ring_3_address

        with ui.list().props("separator").props("width-max"):
            with ui.item():
                with ui.item_section():
                    ui.label("Ring #1 address:").classes("text-bold")
                with ui.item_section():
                    self._ring_1_address = ui.select(options=[]).props("width-max")

                    def on_select(args) -> None:
                        self._ring_1_address_label.text = args.value
                        self._on_ring_1_address(
                            None if args.value == "<not set>" else args.value
                        )

                    self._ring_1_address.on_value_change(on_select)
                # with ui.item_section():
                #     ui.input(label="Manual input")
                with ui.item_section():
                    self._ring_1_address_label = ui.label(
                        midi_config.abs_ring_1
                        if midi_config.abs_ring_1 is not None
                        else "<not set>"
                    )
            with ui.item():
                with ui.item_section():
                    ui.label("Ring #2 address:").classes("text-bold")
                with ui.item_section():
                    self._ring_2_address = ui.select(options=[]).props("width-max")

                    def on_select(args) -> None:
                        self._ring_2_address_label.text = args.value
                        self._on_ring_2_address(
                            None if args.value == "<not set>" else args.value
                        )

                    self._ring_2_address.on_value_change(on_select)
                # with ui.item_section():
                #     ui.input(label="Manual input")
                with ui.item_section():
                    self._ring_2_address_label = ui.label(
                        midi_config.abs_ring_2
                        if midi_config.abs_ring_2 is not None
                        else "<not set>"
                    )
            with ui.item():
                with ui.item_section():
                    ui.label("Ring #3 address:").classes("text-bold")
                with ui.item_section():
                    self._ring_3_address = ui.select(options=[]).props("width-max")

                    def on_select(args) -> None:
                        self._ring_3_address_label.text = args.value
                        self._on_ring_3_address(
                            None if args.value == "<not set>" else args.value
                        )

                    self._ring_3_address.on_value_change(on_select)
                # with ui.item_section():
                #     ui.input(label="Manual input")
                with ui.item_section():
                    self._ring_3_address_label = ui.label(
                        midi_config.abs_ring_3
                        if midi_config.abs_ring_3 is not None
                        else "<not set>"
                    )

    def update_ring_addresses(self, addresses: list[str]) -> None:
        self._ring_1_address.options = addresses + ["<not set>"]
        self._ring_1_address.update()

        self._ring_2_address.options = addresses + ["<not set>"]
        self._ring_2_address.update()

        self._ring_3_address.options = addresses + ["<not set>"]
        self._ring_3_address.update()
