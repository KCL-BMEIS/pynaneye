from collections import deque
import threading
import time
from typing import TypedDict, Optional, Tuple, Union
import queue


class NanEyeFrameDict(TypedDict):
    image_bytes: bytes
    width: int
    height: int
    timestamp: float
    sensor_id: int


class FrameQueue:
    def __init__(self, channel: 'CameraChannel', timestamp_tolerance_us: int = 20000, buffer_size: int = 3):
        self.channel = channel
        if self.channel == 'both':
            if buffer_size < 1:
                raise ValueError("buffer_size must be at least 1")
            self._left_frames: deque[NanEyeFrameDict] = deque(maxlen=buffer_size)
            self._right_frames: deque[NanEyeFrameDict] = deque(maxlen=buffer_size)
            self._lock = threading.Lock()
            self._new_frame_event = threading.Event()
            self._timestamp_tolerance_us = timestamp_tolerance_us
        else:
            self._queue = queue.Queue()

    def put(self, frame: NanEyeFrameDict) -> None:
        if self.channel == 'both':
            with self._lock:
                if frame["sensor_id"] == 0:
                    self._left_frames.append(frame)
                elif frame["sensor_id"] == 1:
                    self._right_frames.append(frame)
                else:
                    print(f"Warning: Unknown sensor_id {frame['sensor_id']}. Frame discarded.")
                    return
                self._new_frame_event.set()
        else:
            self._queue.put(frame)

    def get(self, timeout: Optional[float] = None) -> Union[NanEyeFrameDict, Tuple[NanEyeFrameDict, NanEyeFrameDict]]:
        if self.channel == 'both':
            start_time = time.monotonic()
            while True:
                _ = self._new_frame_event.wait(timeout)
                self._new_frame_event.clear()

                with self._lock:
                    left_frame, right_frame = self._find_and_remove_best_pair()

                    if left_frame and right_frame:
                        return left_frame, right_frame

                    if timeout is not None:
                        elapsed_time = time.monotonic() - start_time
                        remaining_timeout = timeout - elapsed_time
                        if remaining_timeout <= 0:
                            raise queue.Empty("No synchronized stereo pair available within the timeout.")
                        timeout = remaining_timeout
        else:
            return self._queue.get(timeout=timeout)

    def _find_and_remove_best_pair(self) -> Tuple[Optional[NanEyeFrameDict], Optional[NanEyeFrameDict]]:
        best_left_frame: Optional[NanEyeFrameDict] = None
        best_right_frame: Optional[NanEyeFrameDict] = None
        min_time_diff = float("inf")

        current_left_frames = list(self._left_frames)
        current_right_frames = list(self._right_frames)

        for l_frame in current_left_frames:
            for r_frame in current_right_frames:
                time_diff = abs(l_frame["timestamp"] - r_frame["timestamp"])
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_left_frame = l_frame
                    best_right_frame = r_frame

        if best_left_frame and best_right_frame and min_time_diff <= self._timestamp_tolerance_us:
            try:
                self._left_frames.remove(best_left_frame)
            except ValueError:
                pass
            try:
                self._right_frames.remove(best_right_frame)
            except ValueError:
                pass

            return best_left_frame, best_right_frame

        return None, None
