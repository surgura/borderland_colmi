from bleak import BleakScanner, BLEDevice
from colmi_r02_client.cli import DEVICE_NAME_PREFIXES


async def scan_for_rings() -> list[BLEDevice]:
    all_devices = await BleakScanner.discover(timeout=5)
    rings = [
        d
        for d in all_devices
        if d.name and any([d.name.startswith(p) for p in DEVICE_NAME_PREFIXES])
    ]
    return rings
