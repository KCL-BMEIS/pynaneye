# pynaneye

A Python interface for the AMS/Osram [NANO-FIB-BOX_EVM_MO Evaluation Kit](https://ams-osram.com/products/boards-kits-accessories/kits/ams-nano-fib-box-evm-mo-evaluation-kit) for NanEye cameras. Frame from two cameras connected to a evaluation kit cane be streamed to Python simultaneously. 
This package requires a compiled C# DLL to function. The C# source code is included in this repository in the `csharp` directory. You will need to compile this code before you can use the Python interface.

## Prerequisites

To compile the C# library and use `pynaneye`, you will need:

*   A Windows operating system.
*   The .NET Framework 4.8 SDK https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48
*   The AMS/OSRAM NanEye SDK (see below)

## Installation

### 1. Clone this repository or download a release

### 2. Install AMS/Osram SDK

1.  **Download and Install the NanEye C# SDK:**
    *   Visit the product page: [https://ams-osram.com/products/sensor-solutions/cmos-image-sensors/ams-naneyem-miniature-camera-modules](https://ams-osram.com/products/sensor-solutions/cmos-image-sensors/ams-naneyem-miniature-camera-modules)
    *   Direct download link: [https://ams-osram.com/o/download-server/document-download/download/29941803](https://ams-osram.com/o/download-server/document-download/download/29941803)
    *   Install the SDK on your Windows machine.

2.  **Run `install_naneye_dlls.py` (located in the `pynaneye` folder created when you cloned the repo):**
    *   Follow the instructions in the wizard that appears. You will be prompted to select the `lib/x64`, `lib/x86`, or `lib/win32` folder from your SDK installation, depending on your system's architecture.

The script will then copy the required DLLs and firmware files into the `csharp/lib/naneye` directory within this project, enabling the Python application to interface with the camera.

### 3. Compile `pynaneye` with the .NET CLI

Run `build_pynaneye.bat` (or `source build_pynaneye.bat` in Bash). Or:

```bash
cd csharp
dotnet build csharp_naneye.sln -c Release
```

The compiled `PyNanEye.dll` will be located in the `csharp/bin/Release/net48` directory.

### 4. Install into your project's Python environment with pip

`pip install <path to pynaneye>`

or if you want to run the examples, automatically install OpenCV at the same time with

`pip install <path to your pynaneye clone>[examples]`

## Usage

See `example.py`.

## Frame Handling with `FrameQueue`

The `pynaneye.FrameQueue` class provides a mechanism for transferring frames from the camera to your Python application.  Old, unread frames are discarded to ensure the application always has access to the most recent data. When using a dual-sensor setup (`SensorChannel.BOTH`), the `FrameQueue` automatically synchronizes the streams by their timestamps. You can use a FrameQueue to access your frames by subscribing it to the ImageProcessed event:
```python
sensor_channel = SensorChannel.BOTH
camera = Camera(NanEyeSensorType.NanEyeM, sensor_channel)
print("Camera initialized.")

frame_queue = FrameQueue(sensor_channel)
camera.SubscribeToImageProcessedEvent(frame_queue.put)
```

## How it works

This package uses the `pythonnet` library to load and interact with the compiled C# DLL. The Python `Camera` class is a wrapper around the .NET `Camera` class, and it handles the initialization of the .NET runtime.