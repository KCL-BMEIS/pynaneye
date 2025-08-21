from dataclasses import dataclass

import cv2
from numpy import frombuffer, uint8
from numpy._typing import NDArray


def frame_bytes_to_array(frame_bytes: bytes, w: int, h: int) -> NDArray[uint8]:
    """Converts raw frame bytes to a NumPy array."""
    bayer_data = frombuffer(bytearray(frame_bytes), dtype=uint8).reshape((h, w, 3))
    return cv2.cvtColor(bayer_data, cv2.COLOR_RGB2BGR).astype(uint8)


@dataclass
class NanEyeFrame:
    """Dataclass to hold NanEye frame data."""

    image_bytes: bytes
    width: int
    height: int
    timestamp: float
    sensor_id: int

    def as_array(self) -> NDArray[uint8]:
        return frame_bytes_to_array(self.image_bytes, self.width, self.height)
