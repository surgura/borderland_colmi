from colmi_r02_client.client import Client
from bleak import BleakScanner, BLEDevice
import asyncio
from colmi_r02_client.cli import DEVICE_NAME_PREFIXES

def find_devices() -> list[BLEDevice]:
    all_devices = asyncio.run(BleakScanner.discover(timeout=10))
    rings = [d for d in all_devices if d.name and any([d.name.startswith(p) for p in DEVICE_NAME_PREFIXES])]
    return rings

def print_devices() -> None:
    ring_devices = find_devices()
    if len(ring_devices) == 0:
        print("No rings found.")
    else:
        print("Found rings(s)")
        print(f"{'Name':>20}  | Address")
        print("-" * 44)
        for ring in ring_devices:
            print(f"{ring.name:>20}  |  {ring.address}")

def main() -> None:
    # Client()
    print_devices()


if __name__ == "__main__":
    main()