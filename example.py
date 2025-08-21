import threading

import cv2
from numpy import concatenate

from pynaneye import Camera, NanEyeSensorType, SensorChannel
from pynaneye.frame import NanEyeFrame
from pynaneye.frame_queue import FrameQueue


ESCAPE_KEY = 27
SENSOR_CHANNEL = SensorChannel.BOTH  # Or SensorChannel.CH1, SensorChannel.CH2


def display_frames(input_queue: FrameQueue, window_name: str = "NanEye Viewer"):
    """Displays frames from the queue in an openCV window."""
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    while True:
        try:
            frame_data = input_queue.get(timeout=1)
        except Exception:
            break

        if SENSOR_CHANNEL == SensorChannel.BOTH:
            left_frame_dict, right_frame_dict = frame_data
            left_frame = NanEyeFrame(**left_frame_dict)
            right_frame = NanEyeFrame(**right_frame_dict)
            left_image = left_frame.as_array()
            right_image = right_frame.as_array()
            combined_image = concatenate((left_image, right_image), axis=1)
            cv2.imshow(window_name, combined_image)
        else:
            frame = NanEyeFrame(**frame_data)
            image = frame.as_array()
            cv2.imshow(window_name, image)

        key = cv2.waitKey(1) & 0xFF
        if (key == ord('q')) or (key == ESCAPE_KEY):
            break

    cv2.destroyAllWindows()


def run_example():
    try:
        print("Initializing Camera...")
        camera = Camera(NanEyeSensorType.NanEyeM, SENSOR_CHANNEL)
        print("Camera initialized.")

        frame_queue = FrameQueue(SENSOR_CHANNEL)
        camera.SubscribeToImageProcessedEvent(frame_queue.put)

        display_thread = threading.Thread(target=display_frames, args=(frame_queue,))
        display_thread.start()

        print("Starting capture...")
        camera.StartCapture()
        print("Capture started. Press 'q' or 'esc' to quit.")

        display_thread.join()

        print("Stopping capture...")
        camera.StopCapture()
        print("Capture stopped.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the C# DLL is compiled and located correctly, and the camera is connected.")


if __name__ == "__main__":
    run_example()