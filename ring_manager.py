from enum import Enum, auto
from typing import Callable, Awaitable
import asyncio
from bleak import BleakClient, BleakError
from accelerometer_data import AccelerometerData
from datetime import datetime


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
    _on_raw_sensor_data: Callable[[AccelerometerData], Awaitable[None]]

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
        on_raw_sensor_data: Callable[[AccelerometerData], Awaitable[None]],
    ) -> None:
        self._address = address
        self._name = name
        self._on_connect = on_connect
        self._on_disconnect = on_disconnect
        self._on_connecting = on_connecting
        self._on_connect_fail = on_connect_fail
        self._on_raw_sensor_data = on_raw_sensor_data

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
                await self._bleak_client.start_notify(
                    _UART_TX_CHAR_UUID, self._handle_tx
                )
                self._ring_status = RingStatus.CONNECTED
                self._on_connect()

                await self._enable_raw_sensor_data()

                await disconnect_event.wait()
                self._ring_status = RingStatus.DISCONNECTED
                self._on_disconnect()
            except BleakError as e:
                self._ring_status = RingStatus.DISCONNECTED
                self._on_connect_fail(str(e))
            self._bleak_client = None

            if not self._stop_event.is_set():
                await asyncio.sleep(2)

    async def close(self) -> None:
        if self._bleak_client is not None:
            await self._disable_raw_sensor_data()
            await self._bleak_client.disconnect()
        self._stop_event.set()

    @property
    def status(self) -> RingStatus:
        return self._ring_status

    async def _enable_raw_sensor_data(self) -> None:
        await self._send_command(_ENABLE_RAW_SENSOR_CMD)

    async def _disable_raw_sensor_data(self) -> None:
        await self._send_command(_DISABLE_RAW_SENSOR_CMD)

    async def _send_command(self, command):
        await self._bleak_client.write_gatt_char(_UART_RX_CHAR_UUID, command)

    async def _handle_tx(self, sender: int, data: bytearray) -> None:
        if data[0] == 0xA1:
            if data[1] == 0x03:
                # y = axis through charging point
                # z = axis through ring

                acc_x = (data[6] << 4) | (data[7] & 0xF)
                if acc_x & (1 << 11):
                    acc_x -= 1 << 12

                acc_y = (data[2] << 4) | (data[3] & 0xF)
                if acc_y & (1 << 11):
                    acc_y -= 1 << 12

                acc_z = (data[4] << 4) | (data[5] & 0xF)
                if acc_z & (1 << 11):
                    acc_z -= 1 << 12

                await self._on_raw_sensor_data(
                    AccelerometerData(
                        x=acc_x, y=acc_y, z=acc_z, timestamp=datetime.now()
                    )
                )


def _create_command(hex_string):
    bytes_array = [int(hex_string[i : i + 2], 16) for i in range(0, len(hex_string), 2)]
    while len(bytes_array) < 15:
        bytes_array.append(0)
    checksum = sum(bytes_array) & 0xFF
    bytes_array.append(checksum)
    return bytes(bytes_array)


_REBOOT_CMD = _create_command("0801")
_BLINK_TWICE_CMD = _create_command("10")
_ENABLE_RAW_SENSOR_CMD = _create_command("a104")
_DISABLE_RAW_SENSOR_CMD = _create_command("a102")

_UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
_UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
