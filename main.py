from colmi_r02_client.client import Client
from bleak import BleakScanner, BLEDevice
import asyncio
from colmi_r02_client.cli import DEVICE_NAME_PREFIXES
import argparse

def find_devices() -> list[BLEDevice]:
    all_devices = asyncio.run(BleakScanner.discover(timeout=10))
    rings = [d for d in all_devices if d.name and any([d.name.startswith(p) for p in DEVICE_NAME_PREFIXES])]
    return rings

def cmd_scan() -> None:
    print("Scanning..")
    ring_devices = find_devices()
    if len(ring_devices) == 0:
        print("No rings found.")
    else:
        print("Found rings(s)")
        print(f"{'Name':>20}  | Address")
        print("-" * 44)
        for ring in ring_devices:
            print(f"{ring.name:>20}  |  {ring.address}")

def cmd_run(addresses: list[str]) -> None:
    print(f"Running with addresses:\n{'\n'.join(addresses)}")
    raise NotImplementedError()

def cmd_scan_and_run() -> None:
    print("Scanning..")
    ring_devices = find_devices()
    if len(ring_devices) == 0:
        print("No rings found. Exiting..")
        return
    cmd_run([ring.address for ring in ring_devices])

def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan")

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("addresses", nargs="+", help="Addresses to run with")

    scan_and_run_parser = subparsers.add_parser("scan_and_run")

    args = parser.parse_args()

    if args.command == "scan":
        cmd_scan()
    elif args.command == "run":
        cmd_run(args.addresses)
    elif args.command == "scan_and_run":
        cmd_scan_and_run()


if __name__ == "__main__":
    main()