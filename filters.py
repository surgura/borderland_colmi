from filter_abs import FilterAbs, FilterAbsOutput
from accelerometer_data import AccelerometerData
import asyncio
from datetime import timedelta
from typing import AsyncGenerator


class Filters:
    _stop_event: asyncio.Event | None
    _filters_changed_event: asyncio.Event | None

    _abs_filters: dict[str, FilterAbs]
    _abs_filter_gens: dict[str, AsyncGenerator[FilterAbsOutput, None]]

    def __init__(self) -> None:
        self._stop_event = None
        self._filters_changed_event = None
        self._abs_filters = {}
        self._abs_filter_gens = {}

    async def run(self) -> None:
        self._stop_event = asyncio.Event()
        self._filters_changed_event = asyncio.Event()
        while not self._stop_event.is_set():
            stop_wait_task = asyncio.create_task(self._stop_event.wait())
            filters_changed_wait_task = asyncio.create_task(
                self._filters_changed_event.wait()
            )

            abs_filter_tasks = [
                asyncio.Task(g.__anext__()) for g in self._abs_filter_gens.values()
            ]
            abs_filter_addresses = [a for a in self._abs_filter_gens.keys()]

            done, pending = await asyncio.wait(
                [stop_wait_task, filters_changed_wait_task] + abs_filter_tasks,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if stop_wait_task in done:
                break
            if filters_changed_wait_task in done:
                self._filters_changed_event.clear()
            for address, task in zip(
                abs_filter_addresses, abs_filter_tasks, strict=True
            ):
                if task in done:
                    self._on_abs_filter_output(address=address, output=task.result())

            for task in pending:
                task.cancel()
            # TODO get filter answers

    def close(self) -> None:
        self._stop_event.set()

    def on_ring_add(self, address: str) -> None:
        assert address not in self._abs_filters.keys()
        self._abs_filters[address] = FilterAbs(
            update_period=timedelta(milliseconds=100),
            window_size=timedelta(milliseconds=1000),
        )
        self._abs_filter_gens[address] = self._abs_filters[address].run()
        if self._filters_changed_event is not None:
            self._filters_changed_event.set()

    def on_ring_remove(self, address: str) -> None:
        self._abs_filters[address].close()
        del self._abs_filters[address]
        del self._abs_filter_gens[address]
        self._filters_changed_event.set()

    def on_raw_sensor_data(self, address: str, data: AccelerometerData) -> None:
        self._abs_filters[address].on_accelerometer_data(data)

    def _on_abs_filter_output(self, address: str, output: FilterAbsOutput) -> None:
        print(output.value)
