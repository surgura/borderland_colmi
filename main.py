from app import App
from nicegui import ui, app as nicegui_app


def main() -> None:
    # filter_abs = FilterAbs(
    #     update_period=timedelta(milliseconds=100),
    #     window_size=timedelta(milliseconds=1000),
    # )

    # midiout = MidiOut()

    # ui.button("Enable accelerometer", on_click=on_enable_accelerometer)
    # ui.button("Disable accelerometer", on_click=on_disable_accelerometer)

    # line_plot = ui.line_plot(
    #     n=3, limit=100, figsize=(10, 4), update_every=20, layout="constrained"
    # ).with_legend(["x", "y", "z"])

    # line_plot2 = ui.line_plot(
    #     n=1, limit=100, figsize=(10, 4), update_every=1, layout="constrained"
    # ).with_legend(["abs"])

    app = App()

    @nicegui_app.on_startup
    async def startup(self) -> None:
        await app.startup()

    @nicegui_app.on_shutdown
    async def shutdown():
        await app.shutdown()

    ui.run()


if __name__ == "__main__" or __name__ == "__mp_main__":
    main()
