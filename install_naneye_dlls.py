import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import sys

# --- Configuration ---
# The directory where the DLLs should be copied within your project.
# This assumes the script is run from the project's root directory.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
TARGET_DLL_SUBDIR = os.path.join("csharp", "lib", "naneye")
TARGET_DLL_DIR = os.path.join(PROJECT_ROOT, TARGET_DLL_SUBDIR)

# --- User Instructions ---
SDK_DOWNLOAD_LINK = "https://ams-osram.com/o/download-server/document-download/download/29941803"
SDK_PRODUCT_PAGE = "https://ams-osram.com/products/sensor-solutions/cmos-image-sensors/ams-naneyem-miniature-camera-modules"
SDK_LIB_FOLDER = "~/ams/NanEye_EvalSW_API_FiberOpticBox_csharp_pWin_vX-X-X-X/lib"


def run_installer():
    # --- GUI Setup ---
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window

    messagebox.showinfo(
        "NanEye Camera DLL Installer",
        "This script will help you copy the necessary DLLs from the NanEye C# SDK into your project.\n\n"
        "IMPORTANT: The NanEye camera hardware and its DLLs are designed for Windows systems.\n"
        "This script will copy the files, but the Python application using them will only run on Windows."
    )

    messagebox.showinfo(
        "Step 1: Download and Install SDK",
        f"Please download and install the NanEye C# SDK.\n\n"
        f"You can find the direct download link here:\n{SDK_DOWNLOAD_LINK}\n\n"
        f"Or visit the product page for more information:\n{SDK_PRODUCT_PAGE}\n\n"
        "Click OK to continue after installing the SDK."
    )

    messagebox.showinfo(
        "Select DLLs Source Folder",
        "Step 2: Please navigate to your NanEye C# SDK installation directory and select the folder containing the DLLs.\n\n"
        f"This is typically found at {SDK_LIB_FOLDER}\n\n"
        "Please select the appropriate 'x64', 'x86', or 'win32' folder based on your system."
    )

    source_dir = filedialog.askdirectory(
        title="Select the 'lib/x64', 'lib/x86', or 'lib/win32' folder from the NanEye C# SDK"
    )

    if not source_dir:
        messagebox.showerror("Installation Cancelled", "No source directory selected. Exiting installer.")
        sys.exit(1)

    messagebox.showinfo("Source Directory Selected", f"Selected source directory:\n{source_dir}")

    # --- Create Target Directory ---
    try:
        os.makedirs(TARGET_DLL_DIR, exist_ok=True)
        messagebox.showinfo("Target Directory", f"Ensured target directory exists:\n{TARGET_DLL_DIR}")
    except Exception as e:
        messagebox.showerror("Error", f"Could not create target directory:\n{TARGET_DLL_DIR}\n\nError: {e}")
        sys.exit(1)

    # --- Copy DLLs ---
    messagebox.showinfo("Copying DLLs", "Step 3: Copying DLLs...\n\nThis might take a moment.")
    copied_files_count = 0
    errors_occurred = False
    copied_details = []
    error_details = []

    for item_name in os.listdir(source_dir):
        if item_name.lower().endswith(".dll"):
            source_path = os.path.join(source_dir, item_name)
            target_path = os.path.join(TARGET_DLL_DIR, item_name)
            try:
                shutil.copy2(source_path, target_path)  # copy2 preserves metadata
                copied_files_count += 1
                copied_details.append(f"  Copied: {item_name}")
            except Exception as e:
                errors_occurred = True
                error_details.append(f"  Error copying {item_name}: {e}")

    if copied_files_count > 0 and not errors_occurred:
        messagebox.showinfo("Installation Complete", f"Successfully copied {copied_files_count} DLLs to:\n{TARGET_DLL_DIR}\n\nInstallation finished!")
    elif copied_files_count > 0 and errors_occurred:
        messagebox.showwarning("Installation with Warnings", f"Copied {copied_files_count} DLLs, but some errors occurred.\n\n" + "\n".join(error_details))
    else:
        messagebox.showerror("Installation Failed", "No DLLs were found or copied. Please ensure you selected the correct source folder.")
        errors_occurred = True

    if errors_occurred:
        sys.exit(1)


if __name__ == "__main__":
    run_installer()
