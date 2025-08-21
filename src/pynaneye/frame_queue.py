from collections import deque
import threading
from typing import TypedDict, Optional, Tuple, Union
import queue


class NanEyeFrameDict(TypedDict):
    image_bytes: bytes
    width: int
    height: int
    timestamp: float
    sensor_id: int


class FrameQueue:
    """A thread-safe queue for handling frames from a NanEye camera.

    This queue manages frames from either a single channel or two synchronized
    stereo channels ('both' mode). It is designed for real-time applications,
    preventing memory buildup by using a fixed-size buffer and discarding the
    oldest frames when the buffer is full.

    In 'both' mode, it synchronizes frames from the left and right sensors
    by finding the pair with the closest timestamps.

    Defaults:
    - buffer_size: 1 for single channel (FIFO), 3 for 'both' mode.
    """
    def __init__(self, channel: 'CameraChannel', timestamp_tolerance_us: int = 20000, buffer_size: Optional[int] = None):
        self.channel_str = str(channel)

        if buffer_size is None:
            # Need small buffer for matching stereo frames by timestamp
            # Or, if only using one channel, just keep latest frame
            buffer_size = 3 if self.channel_str == 'both' else 1

        if buffer_size < 1:
            raise ValueError("buffer_size must be at least 1")

        self._condition = threading.Condition()
        self._timestamp_tolerance_us = timestamp_tolerance_us

        if self.channel_str == 'both':
            self._left_frames: deque[NanEyeFrameDict] = deque(maxlen=buffer_size)
            self._right_frames: deque[NanEyeFrameDict] = deque(maxlen=buffer_size)
        else:
            # A deque is used as a bounded buffer to hold recent frames.
            self._queue: deque[NanEyeFrameDict] = deque(maxlen=buffer_size)

    def put(self, frame: NanEyeFrameDict) -> None:
        with self._condition:
            if self.channel_str == 'both':
                if frame["sensor_id"] == 0:
                    self._left_frames.append(frame)
                elif frame["sensor_id"] == 1:
                    self._right_frames.append(frame)
                else:
                    print(f"Warning: Unknown sensor_id {frame['sensor_id']}. Frame discarded.")
                    return
            else:
                self._queue.append(frame)
            self._condition.notify()

    def get(self, timeout: Optional[float] = None) -> Union[NanEyeFrameDict, Tuple[NanEyeFrameDict, NanEyeFrameDict]]:
        with self._condition:
            if self.channel_str == 'both':
                pair_found = self._condition.wait_for(self._has_pair, timeout=timeout)
                if pair_found:
                    pair = self._find_and_remove_best_pair()
                    if pair[0] is not None and pair[1] is not None:
                        return pair
                raise queue.Empty("No synchronized stereo pair available within the timeout.")
            else:
                item_found = self._condition.wait_for(lambda: len(self._queue) > 0, timeout=timeout)
                if item_found:
                    return self._queue.popleft()  # FIFO
                else:
                    raise queue.Empty("Queue is empty")

    def _has_pair(self) -> bool:
        """Check if a suitable pair exists without removing them."""
        # This method is called within the condition lock
        for l_frame in self._left_frames:
            for r_frame in self._right_frames:
                if abs(l_frame["timestamp"] - r_frame["timestamp"]) <= self._timestamp_tolerance_us:
                    return True
        return False

    def _find_and_remove_best_pair(self) -> Tuple[Optional[NanEyeFrameDict], Optional[NanEyeFrameDict]]:
        # This method is called within the condition lock
        best_left_frame: Optional[NanEyeFrameDict] = None
        best_right_frame: Optional[NanEyeFrameDict] = None
        min_time_diff = float("inf")

        # Create copies to iterate over while potentially modifying the deques
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
                pass  # Frame might have been pushed out of queue by a new frame already
            try:
                self._right_frames.remove(best_right_frame)
            except ValueError:
                pass  # Frame might have been pushed out of queue by a new frame already

            return best_left_frame, best_right_frame

        return None, None
