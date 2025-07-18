from accelerometer_data import AccelerometerData
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import AsyncGenerator
import asyncio
from collections import deque
import numpy as np


@dataclass
class FilterLeakyIntegratorOutput:
    value: float
    timestamp: datetime


class FilterLeakyIntegrator:
    _stop_event: asyncio.Event | None
    _input_data: deque[AccelerometerData]
    _update_period: timedelta
    _damping: float

    _value: float

    def __init__(self, update_period: timedelta, damping: float) -> None:
        self._stop_event = None
        self._input_data = deque()
        self._update_period = update_period
        self._damping = damping
        self._value = 0.0

    def on_accelerometer_data(self, data: AccelerometerData) -> None:
        absv = max(0.0, np.sqrt(data.x**2 + data.y**2 + data.z**2) - 500)
        # self._value += max(0.0, np.sqrt(data.x**2 + data.y**2 + data.z**2) - 500)
        if absv > 500 and self._value < 0.01:
            self._value = 1.0

    async def run(self) -> AsyncGenerator[FilterLeakyIntegratorOutput, None]:
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

    def _do_loop_iteration(self) -> FilterLeakyIntegratorOutput:
        self._value *= self._damping

        return FilterLeakyIntegratorOutput(
            self._value,
            datetime.now(),
        )

    def close(self) -> None:
        if self._stop_event is not None and not self._stop_event.is_set():
            self._stop_event.set()
