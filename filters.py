from filter_abs import FilterAbs, FilterAbsOutput
from accelerometer_data import AccelerometerData
import asyncio
from datetime import timedelta
from typing import AsyncGenerator, Callable
import traceback


class Filters:
    _stop_event: asyncio.Event | None
    _filters_changed_event: asyncio.Event | None

    _abs_filters: dict[str, FilterAbs]
    _abs_filter_gens: dict[str, AsyncGenerator[FilterAbsOutput, None]]
    _abs_filter_tasks: dict[str, asyncio.Task]

    _on_abs_filter_output: Callable[[FilterAbsOutput], None]

    def __init__(
        self, on_abs_filter_output: Callable[[str, FilterAbsOutput], None]
    ) -> None:
        self._stop_event = None
        self._filters_changed_event = None
        self._abs_filters = {}
        self._abs_filter_gens = {}
        self._on_abs_filter_output = on_abs_filter_output
        self._abs_filter_tasks = {}

    async def run(self) -> None:
        try:
            print()
            self._stop_event = asyncio.Event()
            self._filters_changed_event = asyncio.Event()

            stop_wait_task = asyncio.create_task(self._stop_event.wait())
            filters_changed_wait_task = asyncio.create_task(
                self._filters_changed_event.wait()
            )
            while not self._stop_event.is_set():
                done, pending = await asyncio.wait(
                    [stop_wait_task, filters_changed_wait_task]
                    + [v for v in self._abs_filter_tasks.values()],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                if stop_wait_task in done:
                    break
                if filters_changed_wait_task in done:
                    self._filters_changed_event.clear()
                for address, task in self._abs_filter_tasks.items():
                    if task in done:
                        self._on_abs_filter_output(
                            address=address, output=task.result()
                        )
                        self._abs_filter_tasks[address] = asyncio.create_task(
                            self._abs_filter_gens[address].__anext__()
                        )
        except Exception:
            print("Filters crashed!!!")
            traceback.print_exc()

    def close(self) -> None:
        self._stop_event.set()

    def on_ring_add(self, address: str) -> None:
        assert address not in self._abs_filters.keys()
        self._abs_filters[address] = FilterAbs(
            update_period=timedelta(milliseconds=50),
            window_size=timedelta(milliseconds=500),
        )
        self._abs_filter_gens[address] = self._abs_filters[address].run()
        self._abs_filter_tasks[address] = asyncio.create_task(
            self._abs_filter_gens[address].__anext__()
        )
        if self._filters_changed_event is not None:
            self._filters_changed_event.set()

    def on_ring_remove(self, address: str) -> None:
        self._abs_filters[address].close()
        del self._abs_filters[address]
        del self._abs_filter_gens[address]
        self._abs_filter_tasks[address].cancel()
        del self._abs_filter_tasks[address]
        self._filters_changed_event.set()

    def on_raw_sensor_data(self, address: str, data: AccelerometerData) -> None:
        self._abs_filters[address].on_accelerometer_data(data)
