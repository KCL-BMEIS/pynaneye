# pynaneye

A Python interface for the NanEye camera.

## Prerequisites

This package requires a compiled C# DLL to function. The C# source code is included in this repository in the `csharp` directory. You will need to compile this code before you can use the Python interface.

To compile the C# code, you will need:

*   A Windows operating system.
*   The .NET Framework 4.8 SDK.
*   Microsoft Visual Studio or the .NET CLI.

### Compiling with Visual Studio

1.  Open the `csharp/PyNanEye.sln` solution file in Visual Studio.
2.  Build the solution in "Release" mode.
3.  The compiled `PyNanEye.dll` will be located in the `csharp/bin/Release/net48` directory.

### Compiling with the .NET CLI

```bash
cd csharp
dotnet build -c Release
```

The compiled `PyNanEye.dll` will be located in the `csharp/bin/Release/net48` directory.

## Installation

Once you have compiled the C# code, you can install the Python package using pip:

```bash
pip install .
```

## Usage

```python
from pynaneye import Camera, NanEyeSensorType

camera = Camera(NanEyeSensorType.NanEye2D)
camera.StartCapture()
frame = camera.GetLastFrame()
camera.StopCapture()
```

## How it works

This package uses the `pythonnet` library to load and interact with the compiled C# DLL. The Python `Camera` class is a wrapper around the .NET `Camera` class, and it handles the initialization of the .NET runtime.
