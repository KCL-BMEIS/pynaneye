from collections import deque
import threading
import time
from typing import TypedDict, Optional, Tuple
import queue  # For queue.Empty exception


class NanEyeFrameDict(TypedDict):
    image_bytes: bytes
    width: int
    height: int
    timestamp: float
    sensor_id: int


class StereoFrameQueue:
    """
    A specialized queue for stereo camera frames that maintains only
    the most recent synchronized Left and Right frame pair.

    Frames are paired by finding the two frames (one Left, one Right)
    with the closest timestamps within a specified tolerance.
    Older unmatched frames are automatically discarded as new frames arrive.
    """

    def __init__(self, timestamp_tolerance_us: int = 20000, buffer_size: int = 3):
        """
        Initializes the StereoFrameQueue.

        Args:
            timestamp_tolerance_us (int): The maximum allowed difference in microseconds
                                          between timestamps for two frames to be considered
                                          a synchronized pair. Defaults to 1000 us (1 ms).
            buffer_size (int): The maximum number of individual frames (L or R) to keep
                               in the internal buffers. A larger buffer allows for more
                               robust pairing if frames arrive slightly out of order,
                               but consumes more memory. Must be at least 1.
        """
        if buffer_size < 1:
            raise ValueError("buffer_size must be at least 1")

        # Deques to store incoming left and right frames.
        # maxlen ensures older frames are automatically discarded.
        self._left_frames: deque[NanEyeFrameDict] = deque(maxlen=buffer_size)
        self._right_frames: deque[NanEyeFrameDict] = deque(maxlen=buffer_size)

        self._lock = threading.Lock()  # Protects access to the deques
        # Event to signal when a new frame has arrived, potentially forming a new pair.
        self._new_frame_event = threading.Event()
        self._timestamp_tolerance_us = timestamp_tolerance_us

    def put(self, frame: NanEyeFrameDict) -> None:
        """
        Puts a single frame (left or right) into the queue.

        Args:
            frame (NanEyeFrameDict): The frame object to put.
                                     It must have a 'sensor_id' (0 for Left, 1 for Right)
                                     and a 'timestamp' in microseconds.
        """
        with self._lock:
            if frame["sensor_id"] == 0:  # Assuming 0 for Left sensor
                self._left_frames.append(frame)
            elif frame["sensor_id"] == 1:  # Assuming 1 for Right sensor
                self._right_frames.append(frame)
            else:
                print(f"Warning: Unknown sensor_id {frame['sensor_id']}. Frame discarded.")
                return
            self._new_frame_event.set()  # Signal that a new frame has arrived

    def get(self, timeout: Optional[float] = None) -> Tuple[NanEyeFrameDict, NanEyeFrameDict]:
        """
        Retrieves the most recent synchronized stereo pair.
        Blocks until a pair is available or the timeout occurs.

        Args:
            timeout (Optional[float]): The maximum time to wait for a pair in seconds.
                                       If None, waits indefinitely.

        Returns:
            Tuple[NanEyeFrameDict, NanEyeFrameDict]: A tuple containing
                                                     (left_frame, right_frame) of the synchronized pair.

        Raises:
            queue.Empty: If no synchronized pair is available within the timeout period.
        """
        start_time = time.monotonic()
        while True:
            # Wait for a new frame to arrive or for the specified timeout.
            # If the event times out, it means no new frame was put.
            _ = self._new_frame_event.wait(timeout)

            # Always clear the event after waiting, so the next wait call
            # properly waits for *new* frame arrivals.
            self._new_frame_event.clear()

            with self._lock:
                # Attempt to find and remove the best pair from the current buffers.
                left_frame, right_frame = self._find_and_remove_best_pair()

                if left_frame and right_frame:
                    return left_frame, right_frame

                # If no pair was found after waiting (or if event_set was False):
                if timeout is not None:
                    elapsed_time = time.monotonic() - start_time
                    remaining_timeout = timeout - elapsed_time
                    if remaining_timeout <= 0:
                        # If no time left, raise Empty exception
                        raise queue.Empty("No synchronized stereo pair available within the timeout.")
                    # Update timeout for the next iteration of wait()
                    timeout = remaining_timeout
                # If timeout is None, the loop continues indefinitely until a pair is found.

    def _find_and_remove_best_pair(self) -> Tuple[Optional[NanEyeFrameDict], Optional[NanEyeFrameDict]]:
        """
        Internal method to find the best matching stereo pair (closest timestamps)
        and remove them from their respective internal deques.
        This method assumes the `_lock` is already held by the calling function.

        Returns:
            Tuple[Optional[NanEyeFrameDict], Optional[NanEyeFrameDict]]:
                The (left_frame, right_frame) pair if found and within tolerance,
                otherwise (None, None).
        """
        best_left_frame: Optional[NanEyeFrameDict] = None
        best_right_frame: Optional[NanEyeFrameDict] = None
        min_time_diff = float("inf")

        # Create temporary lists to iterate over, as deques can be modified during iteration
        # if frames are removed.
        current_left_frames = list(self._left_frames)
        current_right_frames = list(self._right_frames)

        # Iterate through all possible combinations of current L and R frames
        # to find the pair with the smallest timestamp difference.
        for l_frame in current_left_frames:
            for r_frame in current_right_frames:
                time_diff = abs(l_frame["timestamp"] - r_frame["timestamp"])
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_left_frame = l_frame
                    best_right_frame = r_frame

        # If a potential best pair was found and its timestamp difference
        # is within the allowed tolerance:
        if best_left_frame and best_right_frame and min_time_diff <= self._timestamp_tolerance_us:
            # Remove the matched frames from their respective deques.
            # Use try-except in case a frame was already removed by another thread
            # or pushed out by maxlen just before this removal attempt.
            try:
                self._left_frames.remove(best_left_frame)
            except ValueError:
                pass  # Frame already gone, no issue.
            try:
                self._right_frames.remove(best_right_frame)
            except ValueError:
                pass  # Frame already gone, no issue.

            return best_left_frame, best_right_frame

        return None, None
