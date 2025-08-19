import threading
from typing import Tuple

import cv2
from numpy import concatenate

from pynaneye import Camera, NanEyeSensorType
from pynaneye.frame import NanEyeFrame
from pynaneye.frame_queue import StereoFrameQueue


ESCAPE_KEY = 27


def display_frames(input_queue: StereoFrameQueue, window_name: str = "NanEye Stereo Viewer"):
    """Displays stereo frames from the queue in an openCV window."""
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    while True:
        frame_pair: Tuple[dict, dict] | None = input_queue.get()
        if frame_pair is None:
            break

        left_frame_dict, right_frame_dict = frame_pair
        left_frame = NanEyeFrame(**left_frame_dict)
        right_frame = NanEyeFrame(**right_frame_dict)

        left_image = left_frame.as_array()
        right_image = right_frame.as_array()

        # Concatenate images side-by-side
        combined_image = concatenate((left_image, right_image), axis=1)

        cv2.imshow(window_name, combined_image)

        key = cv2.waitKey(1) & 0xFF
        if (key == ord('q')) or (key == ESCAPE_KEY):
            break

    cv2.destroyAllWindows()


def run_example():
    try:
        print("Initializing Camera...")
        camera = Camera(NanEyeSensorType.NanEyeM)  # Or NanEyeSensorType.NanEye2D, NanEyeSensorType.NanEyeXS
        print("Camera initialized.")

        # You can provide any Callable that accepts a Python object. The camera will pass each generated frame to the
        # provided callable as a Python dictionary. Here we pass a custom queue designed to pair up frames from two
        # sensors by their timestamps.
        stereo_frame_queue = StereoFrameQueue()
        camera.SubscribeToImageProcessedEvent(stereo_frame_queue.put)

        # We need a new thread to take frames out of the queue as they arrive
        display_thread = threading.Thread(target=display_frames, args=(stereo_frame_queue,))
        display_thread.start()

        print("Starting capture...")
        camera.StartCapture()
        print("Capture started. Press 'q' or 'esc' to quit.")

        display_thread.join()  # Wait for the display thread to finish (i.e. user to press 'q' or 'esc')

        print("Stopping capture...")
        camera.StopCapture()
        print("Capture stopped.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the C# DLL is compiled and located correctly, and the camera is connected.")


if __name__ == "__main__":
    run_example()
