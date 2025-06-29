from nicegui import ui, app
import asyncio
import random
import plotly.graph_objs as go
from client import Client
from datetime import datetime

# plot = ui.plotly({
#     'data': [go.Scatter(x=[], y=[], mode='lines')],
#     'layout': {'title': 'Live Plot'}
# })

# async def on_data(val):
#     x_data.append(asyncio.get_event_loop().time())
#     y_data.append(val)
#     plot.options['data'][0]['x'] = x_data
#     plot.options['data'][0]['y'] = y_data
#     plot.update()

# client.subscribe(on_data)


def run_app(addresses: list[str]) -> None:
    if len(addresses) == 0:
        raise ValueError("Must have at least one address to connect to.")
    print(f"Running with addresses:\n{'\n'.join(addresses)}")

    async def on_enable_accelerometer():
        await client.enable_raw_sensor_data()

    async def on_disable_accelerometer():
        await client.disable_raw_sensor_data()

    async def on_raw_sensor_data(acc_x: int, acc_y: int, acc_z: int):
        now = datetime.now()
        line_plot.push([now], [[acc_x], [acc_y], [acc_z]], y_limits=(-5000, 5000))

    client = Client(address=addresses[0], on_raw_sensor_data=on_raw_sensor_data)

    ui.dark_mode(None)

    ui.button("Enable accelerometer", on_click=on_enable_accelerometer)
    ui.button("Disable accelerometer", on_click=on_disable_accelerometer)

    line_plot = ui.line_plot(
        n=3, limit=100, figsize=(20, 8), update_every=5, layout="constrained"
    ).with_legend(["x", "y", "z"])

    @app.on_startup
    async def startup():
        await client.__aenter__()

    @app.on_shutdown
    async def shutdown():
        await client.__aexit__(None, None, None)

    ui.run()
