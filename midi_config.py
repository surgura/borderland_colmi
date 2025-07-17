from dataclasses import dataclass


@dataclass
class MidiConfig:
    abs_ring_1: str | None = None
    abs_ring_2: str | None = None
    abs_ring_3: str | None = None
