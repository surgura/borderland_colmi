from dataclasses import dataclass
from datetime import datetime


@dataclass
class AccelerometerData:
    x: float
    y: float
    z: float
    timestamp: datetime
