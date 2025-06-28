from __future__ import annotations

from bleak import BleakClient
import logging

logger = logging.getLogger(__name__)

def _create_command(hex_string):
    bytes_array = [int(hex_string[i:i+2], 16) for i in range(0, len(hex_string), 2)]
    while len(bytes_array) < 15:
        bytes_array.append(0)
    checksum = sum(bytes_array) & 0xFF
    bytes_array.append(checksum)
    return bytes(bytes_array)

_ENABLE_RAW_SENSOR_CMD = _create_command("a104")

_UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
_UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

class Client:
    address: str
    bleak_client: BleakClient

    def __init__(self, address: str) -> None:
        self.address = address
        self.bleak_client = BleakClient(self.address)

    async def __aenter__(self) -> Client:
        logger.info(f"Connecting to {self.address}")
        await self.connect()
        logger.info("Connected!")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        logger.info("Disconnecting")
        if exc_val is not None:
            logger.error("Error in client. Disconnecting.. error will be shown afterwards.")
        await self.disconnect()

    async def connect(self) -> None:
        await self.bleak_client.connect()

        # nrf_uart_service = self.bleak_client.services.get_service(UART_SERVICE_UUID)
        # assert nrf_uart_service
        # rx_char = nrf_uart_service.get_characteristic(_UART_RX_CHAR_UUID)
        # assert rx_char
        # self.rx_char = rx_char
        await self.bleak_client.start_notify(_UART_TX_CHAR_UUID, self._handle_tx)

    async def disconnect(self) -> None:
        await self.bleak_client.disconnect()

    async def enable_raw_sensor_data(self) -> None:
        await self._send_command(_ENABLE_RAW_SENSOR_CMD)

    async def _handle_tx(self, sender: int, data: bytearray) -> None:
        # logger.info("Got tx")
        print("got tx")

    async def _send_command(self, command):
        await self.bleak_client.write_gatt_char(_UART_RX_CHAR_UUID, command)