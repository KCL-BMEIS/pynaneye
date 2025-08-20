# pynaneye

A Python interface for the AMS/Osram NanEye evaluation kit.

## Prerequisites

This package requires a compiled C# DLL to function. The C# source code is included in this repository in the `csharp` directory. You will need to compile this code before you can use the Python interface.

To compile the C# code, you will need:

*   A Windows operating system.
*   The .NET Framework 4.8 SDK https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48
*   The AMS/OSRAM NanEye SDK (see below)

### AMS/OSRAM NanEye SDK Installation

1.  **Download and Install the NanEye C# SDK:**
    *   Visit the product page: [https://ams-osram.com/products/sensor-solutions/cmos-image-sensors/ams-naneyem-miniature-camera-modules](https://ams-osram.com/products/sensor-solutions/cmos-image-sensors/ams-naneyem-miniature-camera-modules)
    *   Direct download link: [https://ams-osram.com/o/download-server/document-download/download/29941803](https://ams-osram.com/o/download-server/document-download/download/29941803)
    *   Install the SDK on your Windows machine.

2.  **Run `install_naneye_dlls.py`:**
    *   Follow the instructions in the wizard that appears. You will be prompted to select the `lib/x64`, `lib/x86`, or `lib/win32` folder from your SDK installation, depending on your system's architecture.

The script will then copy the required DLLs and firmware files into the `csharp/lib/naneye` directory within this project, enabling the Python application to interface with the camera.

### Compiling with the .NET CLI

Run `build_pynaneye.bat` (or `source build_pynaneye.bat` in Bash). Or:

```bash
cd csharp
dotnet build csharp_naneye.sln -c Release
```

The compiled `PyNanEye.dll` will be located in the `csharp/bin/Release/net48` directory.

### Usage

See `example.py`.

### How it works

This package uses the `pythonnet` library to load and interact with the compiled C# DLL. The Python `Camera` class is a wrapper around the .NET `Camera` class, and it handles the initialization of the .NET runtime.
