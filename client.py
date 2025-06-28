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

_REBOOT_CMD = _create_command("0801")
_BLINK_TWICE_CMD = _create_command("10")
_ENABLE_RAW_SENSOR_CMD = _create_command("a104")
_DISABLE_RAW_SENSOR_CMD = _create_command("a102")

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

    async def reboot(self) -> None:
        await self._send_command(_REBOOT_CMD)

    async def blink_twice(self) -> None:
        await self._send_command(_BLINK_TWICE_CMD)

    async def enable_raw_sensor_data(self) -> None:
        await self._send_command(_ENABLE_RAW_SENSOR_CMD)

    async def disable_raw_sensor_data(self) -> None:
        await self._send_command(_DISABLE_RAW_SENSOR_CMD)

    async def _handle_tx(self, sender: int, data: bytearray) -> None:
        # logger.info("Got tx")
        # print("got tx")
        # print(data)
        parsed_data = {
            "payload": "", "accX": "", "accY": "", "accZ": "",
            "ppg": "", "ppg_max": "", "ppg_min": "", "ppg_diff": "",
            "spO2": "", "spO2_max": "", "spO2_min": "", "spO2_diff": ""
        }
        
        # Store the payload as a hex string
        parsed_data["payload"] = data.hex()

        # Update parsed_data based on the sensor type
        if data[0] == 0xA1:
            subtype = data[1]
            if subtype == 0x01:
                parsed_data["spO2"] = (data[2] << 8) | data[3]
                parsed_data["spO2_max"] = data[5]
                parsed_data["spO2_min"] = data[7]
                parsed_data["spO2_diff"] = data[9]
            elif subtype == 0x02:
                parsed_data["ppg"] = (data[2] << 8) | data[3]
                parsed_data["ppg_max"] = (data[4] << 8) | data[5]
                parsed_data["ppg_min"] = (data[6] << 8) | data[7]
                parsed_data["ppg_diff"] = (data[8] << 8) | data[9]
            elif subtype == 0x03:
                parsed_data["accX"] = ((data[6] << 4) | (data[7] & 0xF)) - (1 << 11) if data[6] & 0x8 else ((data[6] << 4) | (data[7] & 0xF))
                parsed_data["accY"] = ((data[2] << 4) | (data[3] & 0xF)) - (1 << 11) if data[2] & 0x8 else ((data[2] << 4) | (data[3] & 0xF))
                parsed_data["accZ"] = ((data[4] << 4) | (data[5] & 0xF)) - (1 << 11) if data[4] & 0x8 else ((data[4] << 4) | (data[5] & 0xF))
            
            # Check if ppg and spO2 are equal to zero; skip writing if true
            if parsed_data["ppg"] == 0 or parsed_data["spO2"] == 0:
                print("Skipping data with zero ppg and spO2 values")
                return

            # timestamp = datetime.now().isoformat()
            # csv_writer.writerow([timestamp] + [parsed_data.get(col, "") for col in parsed_data])
            print("Written to CSV:", [parsed_data.get(col, "") for col in parsed_data])  # Confirm write

    async def _send_command(self, command):
        await self.bleak_client.write_gatt_char(_UART_RX_CHAR_UUID, command)