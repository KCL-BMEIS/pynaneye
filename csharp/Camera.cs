using Awaiba.Drivers.Grabbers;
using Awaiba.Drivers.Grabbers.Events;
using Awaiba.Algorithms;
using Awaiba.Data;
using System.Reflection;
using System.Diagnostics;
using System.Threading;
using System.Collections.Generic;
using System.IO;
using System;
using Python.Runtime;
using Awaiba.FrameProcessing;
using System.Linq;

namespace System.Windows.Forms
{
    public class Form { }  // Dummy placeholder to force inclusion of Forms dependency
}

namespace PyNanEye
{

    public enum NanEyeSensorType
    {
        NanEye2D,
        NanEyeM,
        NanEyeXS
    }

    public class Camera
    {
        private NanEyeMusb3_FobProvider provider = new NanEyeMusb3_FobProvider();
        private List<AutomaticExposureControlHardware> allAEC = new List<AutomaticExposureControlHardware>();
        private OnImageReceivedBitmapEventArgs lastFrame = null;

    public Camera()
        {
            /*** To Choose the correct files to program firmware and FPGA ***/
            ///To program the FPGA with the bin file and the FW file
            ///You can choose the folder/file combination where the files are
            ///
   
            string dllDirectoryPath = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location ?? string.Empty);
            if (string.IsNullOrEmpty(dllDirectoryPath))
            {
                Console.WriteLine("Error: Could not determine PyNanEye.dll location");
                return;
            }
            string firmwareDirectory = Path.Combine(dllDirectoryPath, @"firmware");
            provider.SetFWFile(Path.Combine(firmwareDirectory, @"fx3_fw_2EP.img"));
            provider.SetFpgaFile(Path.Combine(firmwareDirectory, @"fob_fpga_v08.bin"));
            //Runtime.PythonDLL = Path.Combine(dllDirectoryPath, @"python312.dll");
            //PythonEngine.Initialize();
            //PythonEngine.BeginAllowThreads();

            /*** To choose the sensors to get data from ***/
            ///If you want to receive data from it, please put it at true, else, put it at false
            ///The sensors are organized in the code as in the Documentation, regarding the Sensor 1 and Sensor 2
            provider.Sensors = new List<bool>
            {
                true,
                true
            };

            /*** Configure the color conversion (demosaicing from Bayer to RGB). BayerGrid 0 is specific to NanEyeM ***/
            foreach (var pr in ProcessingWrapper.pr)
            {
                pr.colorReconstruction.SetBayerGrid(0);
                pr.colorReconstruction.pixelAdjustment.RedGain = 0.95f;
                pr.colorReconstruction.pixelAdjustment.GreenTopGain = 0.84f;
                pr.colorReconstruction.pixelAdjustment.GreenBottomGain = 0.84f;
                pr.colorReconstruction.pixelAdjustment.BlueGain = 1.25f;
            }

            /*** Event Handlers to get the image and handle the exceptions from the bottom layers ***/
            provider.ImageProcessed += OnProviderImageProcessed;
            provider.Exception += OnProviderException;
        }

        public Camera(NanEyeSensorType sensorType)
            : this()  // Call the default constructor to reuse initialization logic
        {
            this.sensorType = sensorType;
        }

        private NanEyeSensorType sensorType;

        public NanEyeSensorType SensorType
        {
            get => sensorType;
            set => sensorType = value;
        }

        private void OnProviderImageProcessed(object sender, OnImageReceivedBitmapEventArgs e)
        {
            // This print is for checking the pixel data between CS and Python
            // Console.WriteLine(BitConverter.ToString(e.PixelData.Take(9).ToArray()));
            lastFrame = e;
        }

        public void SubscribeToImageProcessedEvent(PyObject callback)
        {
            void handler(object sender, OnImageReceivedBitmapEventArgs e)
            {
                using (Py.GIL())
                {
                    dynamic imageData = new Python.Runtime.PyDict();
                    PyObject builtins = Py.Import("builtins");
                    PyObject bytes = builtins.GetAttr("bytes");
                    PyObject imageBytes = bytes.Invoke(e.PixelData.ToPython());
                    imageData["image_bytes"] = imageBytes;
                    imageData["width"] = new PyInt(e.Width);
                    imageData["height"] = new PyInt(e.Height);
                    imageData["timestamp"] = new PyFloat(e.FramesTime);
                    imageData["sensor_id"] = new PyInt(e.SensorID);
                    callback.Invoke(imageData);
                }
            }

            provider.ImageProcessed += handler;
        }

        public Tuple<byte[], int, int, byte> GetLastFrame()
        {
            if (lastFrame == null)
            {
                byte[] noFrame = Array.Empty<byte>();
                return Tuple.Create(noFrame, 0, 0, (byte)0);
            }
            return Tuple.Create(lastFrame.PixelData ?? Array.Empty<byte>(), lastFrame.Width, lastFrame.Height, lastFrame.BitsPerPixel);
        }

        private void OnProviderException(object sender, OnExceptionEventArgs e)
        {
            Console.WriteLine($"NanEye provider exception! {e.ex}");
        }

        public void StartCapture()
        {
            Console.WriteLine("Starting Capture!");
            provider.StartCapture();
        }

        public void StopCapture()
        {
            provider.StopCapture();
        }

        private void WriteRegisterBothCameras(int address, int value, bool isSensorRegister = true)
        {
            provider.WriteRegister(new RegisterPayload
            {
                Address = address,
                SensorID = 0,
                Value = value,
                IsSensorRegister = isSensorRegister
            });
            provider.WriteRegister(new RegisterPayload
            {
                Address = address,
                SensorID = 1,
                Value = value,
                IsSensorRegister = isSensorRegister
            });
        }

        public void SetGain(int value)
        {
            if (value < 0 || value > 160)
                throw new ArgumentOutOfRangeException(nameof(value), "Gain must be between 0 and 160.");
            WriteRegisterBothCameras(0x01, value);
        }

        public void SetOffset(int value)
        {
            if (value < 0 || value > 255)
                throw new ArgumentOutOfRangeException(nameof(value), "Offset must be between 0 and 255.");
            WriteRegisterBothCameras(0x02, value);
        }

        public void SetExposure(int value)
        {
            int min = 0, max = 0;
            switch (sensorType)
            {
                case NanEyeSensorType.NanEye2D:
                    min = 1; max = 249; break;
                case NanEyeSensorType.NanEyeM:
                    min = 0; max = 159; break;
                case NanEyeSensorType.NanEyeXS:
                    min = 0; max = 99; break;
            }

            if (value < min || value > max)
                throw new ArgumentOutOfRangeException(nameof(value), $"Exposure must be between {min} and {max} for sensor type '{sensorType}'.");

            WriteRegisterBothCameras(0x03, value);
        }

        public void SetFrameRate(int value)
        {
            switch (sensorType)
            {
                case NanEyeSensorType.NanEye2D:
                    if (value < 1600 || value > 2400)
                        throw new ArgumentOutOfRangeException(nameof(value), "Frame rate for 2D sensors must be between 1600 and 2400 (representing 16.00–24.00 FPS).");
                    WriteRegisterBothCameras(0x04, value, isSensorRegister: false);
                    break;

                case NanEyeSensorType.NanEyeM:
                    if (value < 0 || value > 5)
                        throw new ArgumentOutOfRangeException(nameof(value), "Frame rate for M sensors must be between 0 and 5 FPS.");
                    WriteRegisterBothCameras(0x21, value, isSensorRegister: true);
                    break;

                case NanEyeSensorType.NanEyeXS:
                    if (value < 0 || value > 2)
                        throw new ArgumentOutOfRangeException(nameof(value), "Frame rate for XS sensors must be between 0 and 2 FPS.");
                    WriteRegisterBothCameras(0x21, value, isSensorRegister: true);
                    break;
            }
        }

        private void SetAECDefaultSettings(AutomaticExposureControlHardware aec)
        {
            aec.TargetGreyValue = 560;
            aec.Hysteresis = 63;
            aec.StepSize = 2;
            aec.FrameNumber = 0;
            aec.IsEnabled = true;
            aec.ShowROI = 0;
            aec.TopROI = 64;
            aec.RightROI = 256;
            aec.LeftROI = 64;
            aec.BottomROI = 256;
        
            aec.MinExpValueGain0 = 0;
            aec.HighExpValueGain0 = 140;
            aec.MaxExpValueGain0 = 160;
        
            aec.MinExpValueGain1 = 110;
            aec.LowExpValueGain1 = 125;
            aec.HighExpValueGain1 = 140;
            aec.MaxExpValueGain1 = 160;
        
            aec.MinExpValueGain2 = 110;
            aec.LowExpValueGain2 = 135;
            aec.HighExpValueGain2 = 140;
            aec.MaxExpValueGain2 = 160;
        
            aec.MinExpValueGain3 = 110;
            aec.LowExpValueGain3 = 115;
            aec.MaxExpValueGain3 = 160;
        }

        public void EnableAutomaticExposureControl()
        {
            for (int i = 0; i < 2; i++)
            {
                allAEC[i].IsEnabled = true;
            }

        }

        public void DisableAutomaticExposureControl()
        {
            for (int i = 0; i < 2; i++)
            {
                allAEC[i].IsEnabled = false;
            }

        }

        public void ReconfigureAutomaticExposureControl()
        {
            /*** For automatic exposure control ***/
            /// One algorithm for each of the two camera channels
            var t0 = Stopwatch.GetTimestamp();
            for (int i = 0; i < 2; i++)
            {
                allAEC.Add(new AutomaticExposureControlHardware(i));
                allAEC[i].SensorId = i;
            }
            Console.WriteLine($"AEC algos created after {(Stopwatch.GetTimestamp() - t0) / (double)Stopwatch.Frequency} seconds");
            provider.SetAutomaticExpControl(allAEC);
            Console.WriteLine($"AEC algos applied to provider after {(Stopwatch.GetTimestamp() - t0) / (double)Stopwatch.Frequency} seconds");
            foreach (var aec in allAEC)
            {
                SetAECDefaultSettings(aec);
            }
            Console.WriteLine($"AEC default settings applied after {(Stopwatch.GetTimestamp() - t0) / (double)Stopwatch.Frequency} seconds");
        }

        public void EnableColourReconstruction()
        {
            Console.WriteLine($"Color reconstruction enabled");
            ProcessingWrapper.pr[0].colorReconstruction.Apply = true;
            ProcessingWrapper.pr[1].colorReconstruction.Apply = true;
        }

        public void DisableColourReconstruction()
        {
            Console.WriteLine($"Color reconstruction disabled");
            ProcessingWrapper.pr[0].colorReconstruction.Apply = false;
            ProcessingWrapper.pr[1].colorReconstruction.Apply = false;
        }
    }
}
