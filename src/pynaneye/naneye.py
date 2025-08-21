import sys
import os
import shutil
import platform
from enum import Enum
from typing import Callable, Optional

# --- Globals to hold the real .NET types once loaded ---
_Camera: Optional[Callable] = None
_NanEyeSensorType: Optional[Enum] = None
_CameraChannel: Optional[Enum] = None
_dotnet_initialized = False


def _initialize_dotnet_runtime():
    """
    Loads the .NET runtime and imports the C# classes.
    This is called lazily when the hardware classes are first used.
    """
    global _Camera, _CameraChannel, _NanEyeSensorType, _dotnet_initialized
    if _dotnet_initialized:
        return

    # On non-Windows systems, hardware access is not possible.
    # Raise an error to prevent further execution.
    if platform.system() != "Windows":
        raise NotImplementedError("The NanEye camera hardware is only supported on Windows.")

    import pythonnet

    DLL_NAME = "PyNanEye.dll"
    DOTNET_LIB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../csharp/lib/naneye"))
    DOTNET_BUILD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../csharp/bin/Release/net48"))

    src_file = os.path.join(DOTNET_BUILD_DIR, DLL_NAME)
    dst_file = os.path.join(DOTNET_LIB_DIR, DLL_NAME)

    try:
        shutil.copy(src_file, dst_file)
    except FileNotFoundError:
        print(
            f"Could not update DLL from the Visual Studio build directory. Using version already in the lib directory."
        )

    if DOTNET_LIB_DIR not in sys.path:
        sys.path.insert(0, DOTNET_LIB_DIR)

    pythonnet.set_runtime("netfx")
    pythonnet.load()

    import clr

    clr.AddReference(DLL_NAME.split(".")[0])

    # Import the C# classes and assign them to the global variables
    from PyNanEye import Camera as DotNetCamera
    from PyNanEye import NanEyeSensorType as DotNetSensorType
    from PyNanEye import CameraChannel as DotNetCameraChannel

    _Camera = DotNetCamera
    _NanEyeSensorType = DotNetSensorType
    _CameraChannel = DotNetCameraChannel
    _dotnet_initialized = True


class Camera:
    """
    A wrapper class for the .NET Camera object.
    It ensures the .NET runtime is loaded before the camera is accessed.
    """

    def __new__(cls, *args, **kwargs):
        _initialize_dotnet_runtime()
        # Create an instance of the real .NET camera class
        return _Camera(*args, **kwargs)


class CameraChannel:
    """
    A wrapper class for the .NET CameraChannel Enum.
    It ensures the .NET runtime is loaded before the camera is accessed.
    """
    def __getattribute__(self, name):
        _initialize_dotnet_runtime()
        # Get the attribute from the real .NET Enum class
        return getattr(_CameraChannel, name)


# Instantiate the wrapper to make it behave like an enum object
CameraChannel = CameraChannel()  # type: ignore


class NanEyeSensorType:
    """
    A wrapper for the .NET NanEyeSensorType Enum.
    It ensures the .NET runtime is loaded before the enum is accessed.
    """

    def __getattribute__(self, name):
        _initialize_dotnet_runtime()
        # Get the attribute from the real .NET Enum class
        return getattr(_NanEyeSensorType, name)


# Instantiate the wrapper to make it behave like an enum object
NanEyeSensorType = NanEyeSensorType()  # type: ignore

# The main block is useful for testing the .NET connection directly
if __name__ == "__main__":
    try:
        _initialize_dotnet_runtime()
        import clr

        # noinspection PyUnresolvedReferences
        from System import Environment, Console

        clr.AddReference("System")
        Console.WriteLine("Hello from the C# console!")
        print(f'Is the .NET CLR 64 bit? {"Yes" if Environment.Is64BitProcess else "No"}')
    except Exception as e:
        print(f"An error occurred during .NET initialization: {e}")
