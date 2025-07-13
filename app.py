from nicegui import ui, app
from client import Client
from datetime import datetime, timedelta
from filter_abs import FilterAbs
import asyncio
from accelerometer_data import AccelerometerData
from rtmidi import MidiOut


async def filter_abs_task(filter_abs: FilterAbs, plot, midi: MidiOut) -> None:
    async for abs_output in filter_abs.run():
        plot.push([abs_output.timestamp], [[abs_output.value]], y_limits=(0, 3000))
        print("send!")
        midi.send_message(
            [176, 1, round((min(2500, max(0, abs_output.value - 500))) / 2500 * 127)]
        )


def run_app(addresses: list[str]) -> None:
    filter_abs = FilterAbs(
        update_period=timedelta(milliseconds=100),
        window_size=timedelta(milliseconds=1000),
    )

    midiout = MidiOut()

    if len(addresses) == 0:
        raise ValueError("Must have at least one address to connect to.")
    print(f"Running with addresses:\n{'\n'.join(addresses)}")

    async def on_enable_accelerometer():
        await client.enable_raw_sensor_data()

    async def on_disable_accelerometer():
        await client.disable_raw_sensor_data()

    async def on_raw_sensor_data(acc_x: int, acc_y: int, acc_z: int):
        now = datetime.now()
        accelerometer_data = AccelerometerData(x=acc_x, y=acc_y, z=acc_z, timestamp=now)
        filter_abs.on_accelerometer_data(accelerometer_data)
        # line_plot.push([now], [[acc_x], [acc_y], [acc_z]], y_limits=(-5000, 5000))

    client = Client(address=addresses[0], on_raw_sensor_data=on_raw_sensor_data)

    ui.dark_mode(None)

    ui.button("Enable accelerometer", on_click=on_enable_accelerometer)
    ui.button("Disable accelerometer", on_click=on_disable_accelerometer)

    line_plot = ui.line_plot(
        n=3, limit=100, figsize=(10, 4), update_every=20, layout="constrained"
    ).with_legend(["x", "y", "z"])

    line_plot2 = ui.line_plot(
        n=1, limit=100, figsize=(10, 4), update_every=1, layout="constrained"
    ).with_legend(["abs"])

    @app.on_startup
    async def startup():
        await client.__aenter__()
        midiout.open_virtual_port("My midi thing")
        asyncio.create_task(filter_abs_task(filter_abs, line_plot2, midiout))

    @app.on_shutdown
    async def shutdown():
        await client.__aexit__(None, None, None)

    ui.run()
