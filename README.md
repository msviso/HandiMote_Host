# MSVison HandiMote Demo Console
## Introduction
Welcome to the MSVison HandiMote Demo Console! This application allows you to interact with the HandiMote device, which consists of two applications: one for the gray level image matrix and one for the 6DoF motion sensor orientation output. Both data streams are transmitted using BLE (Bluetooth Low Energy) notification update rate time. Additionally, the application supports UART channel communication.

## Getting Started
Device Connection
To use the MSVison HandiMote Demo Console, you need to connect it to your HandiMote device. Follow these steps to establish a connection:

Make sure your HandiMote device is powered on and within range of your computer.
Launch the MSVison HandiMote Demo Console application.
Select your HandiMote device from the list of available devices.
Once connected, you will see a confirmation message indicating successful connection.
### Console Interface
The MSVison HandiMote Demo Console provides the following interface elements:

Image Display: Displays the real-time gray level image matrix captured by the HandiMote device.
IMU Visualization: Shows the orientation of the device using a 3D visualization of a flying plant.
Message Box: Provides a scrollable text area for displaying messages and status updates.
Buttons:
Capture Image: Allows you to capture and save the current image as a PNG file.
Swap Packages: Use this button if the image appears broken to swap image data packages.
Close Demo: Closes the console and disconnects from the HandiMote device.
### Usage
#### Image Capture
To capture an image from the HandiMote device:

*Click the Capture Image button.*
* The captured image will be saved to the specified directory as a PNG file.
* Package Swapping
If the displayed image appears broken or distorted, you can try swapping image 

*data packages by following these steps:*

* Click the Swap Packages button.
* Check if the image quality improves after swapping packages.

*Closing the Demo*

*To close the MSVison HandiMote Demo Console and disconnect from the HandiMote device:*

1. Click the Close Demo button.

2. Confirm the action if prompted.

3. The console will be closed, and the connection to the device will be terminated.

Requirements

* Python 3.x

* Required Python libraries (install via pip):

* opencv-python

* numpy

* asyncio
  
* bleak
* tkinter
* PIL
* quaternion
* matplotlib

#### Notes
* Make sure your HandiMote device is properly configured and powered on before attempting to connect.
  
* Ensure that your computer has Bluetooth functionality enabled and that it is discoverable.
* If you encounter any issues or have questions, refer to the documentation or contact support.
