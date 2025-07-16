from accelerometer_data import AccelerometerData
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import AsyncGenerator
import asyncio
from collections import deque
import numpy as np


@dataclass
class FilterAbsOutput:
    value: float
    timestamp: datetime


class FilterAbs:
    """
    Ingests accelerometer xyz, possibly with missing samples & inconsistent period, outputs approximate absolute value at a consistent period.
    """

    _stop_event: asyncio.Event | None
    _input_data: deque[AccelerometerData]
    _update_period: timedelta
    _window_size: timedelta

    def __init__(self, update_period: timedelta, window_size: timedelta) -> None:
        self._stop_event = None
        self._input_data = deque()
        self._update_period = update_period
        self._window_size = window_size

    def set_update_period(self, update_period: timedelta) -> None:
        self._update_period = update_period

    def set_window_size(self, window_size: timedelta) -> None:
        self._window_size = window_size

    def on_accelerometer_data(self, data: AccelerometerData) -> None:
        self._input_data.append(data)

    async def run(self) -> AsyncGenerator[FilterAbsOutput, None]:
        self._stop_event = asyncio.Event()

        while True:
            stop_wait_task = asyncio.create_task(self._stop_event.wait())
            timer_task = asyncio.create_task(
                asyncio.sleep(self._update_period.total_seconds())
            )

            done, pending = await asyncio.wait(
                [stop_wait_task, timer_task], return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            if stop_wait_task in done:
                break

            yield self._do_loop_iteration()

    def _do_loop_iteration(self) -> FilterAbsOutput:
        now = datetime.now()
        while (
            len(self._input_data) > 0
            and now - self._input_data[0].timestamp > self._window_size
        ):
            self._input_data.popleft()

        mean = (
            0.0
            if len(self._input_data) == 0
            else np.mean([np.sqrt(d.x**2 + d.y**2 + d.z**2) for d in self._input_data])
        )

        return FilterAbsOutput(
            mean,
            datetime.now(),
        )

    def close(self) -> None:
        if self._stop_event is not None and not self._stop_event.is_set():
            self._stop_event.set()
