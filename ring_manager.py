from enum import Enum, auto
from typing import Callable
import asyncio
from bleak import BleakClient, BleakError


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
    _on_connect_fail: Callable[[str], None]

    _ring_status: RingStatus

    _bleak_client: BleakClient | None

    _stop_event: asyncio.Event | None

    def __init__(
        self,
        address: str,
        name: str,
        on_connect: Callable[[], None],
        on_disconnect: Callable[[], None],
        on_connecting: Callable[[], None],
        on_connect_fail: Callable[[str], None],
    ) -> None:
        self._address = address
        self._name = name
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_connecting = on_connecting
        self._on_connect_fail = on_connect_fail

        self._stop_event = None

        self._ring_status = RingStatus.DISCONNECTED

        self._bleak_client = None

    @property
    def address(self) -> str:
        return self._address

    @property
    def name(self) -> str:
        return self._name

    async def run(self) -> None:
        self._stop_event = asyncio.Event()

        while not self._stop_event.is_set():
            self._ring_status = RingStatus.CONNECTING
            self._on_connecting()

            disconnect_event = asyncio.Event()
            try:
                self._bleak_client = BleakClient(
                    self._address,
                    disconnected_callback=lambda c: disconnect_event.set(),
                )
                await self._bleak_client.connect()
                self._ring_status = RingStatus.CONNECTED
                self._on_connect()

                await disconnect_event.wait()
                self._ring_status = RingStatus.DISCONNECTED
                self._on_disconnect()
            except BleakError as e:
                self._ring_status = RingStatus.DISCONNECTED
                self._on_connect_fail(str(e))
            except Exception:
                print("exception while connecting/connected")
            self._bleak_client = None
            await asyncio.sleep(2)

    async def close(self) -> None:
        if self._bleak_client is not None:
            await self._bleak_client.disconnect()
        self._stop_event.set()

    @property
    def status(self) -> RingStatus:
        return self._ring_status
