from rtmidi import MidiOut as RtMidiOut


class MidiOut:
    _midi_out: RtMidiOut

    def __init__(self) -> None:
        self._midi_out = RtMidiOut(name="borderland_pandelirium_rings")
        self._midi_out.open_virtual_port("borderland_pandelirium_rings")

    def send_abs_1(self, value: float) -> None:
        """
        value must be between 0 and 1
        """
        assert value <= 1.0 and value >= 0.0
        self._midi_out.send_message([176, 1, round(value * 127)])

    def send_abs_2(self, value: float) -> None:
        """
        value must be between 0 and 1
        """
        assert value <= 1.0 and value >= 0.0
        self._midi_out.send_message([177, 1, round(value * 127)])

    def send_abs_(self, value: float) -> None:
        """
        value must be between 0 and 1
        """
        assert value <= 1.0 and value >= 0.0
        self._midi_out.send_message([178, 1, round(value * 127)])
