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

#### Device Information
* Device Name (UUID): HandiMote
* UUID for Gray Level Image Matrix Application: f3645566-00b0-4240-ba50-05ca45bf8abc
* UUID for 6DoF Motion Sensor Orientation Application: f3645571-00b0-4240-ba50-05ca45bf8abc
* UUID for UART Service: 6e400001-b5a3-f393-e0a9-e50e24dcca9e
* UUID for UART RX Characteristic: 6e400002-b5a3-f393-e0a9-e50e24dcca9e (RX for the device to receive data)
* UUID for UART TX Characteristic: 6e400003-b5a3-f393-e0a9-e50e24dcca9e (TX for the device to send data)

#### Connection Instructions
1. Launch the Application: Open the MSVison HandiMote Demo Console application on your computer.
2. Scan for Devices: Click on the "Scan" button within the application to scan for available BLE devices.
3. Select HandiMote Device: From the list of discovered devices, select the device named "HandiMote."
4. Establish Connection: Once the HandiMote device is selected, click on the "Connect" button to establish a connection.
5. Notification Subscriptions: After connecting, the application will automatically subscribe to notifications for the gray level image matrix, motion sensor orientation, and UART data characteristics.
6. Interaction: You can now interact with the HandiMote device through the application interface, capturing images, viewing orientation data, and sending/receiving UART commands.
   
> Notes
Ensure that your HandiMote device is powered on and within range of your computer during the connection process.
If you encounter any issues with the connection, ensure that Bluetooth is enabled on your computer and that the HandiMote device is in pairing mode.
Refer to the application documentation for troubleshooting steps and additional information.


### Image Matrix Configuration

* Default Image Matrix Size: 24x20 pixels

* Data Type: uint8_t (unsigned integer, 8 bits per pixel)

* Data Stream Size: Due to the BLE MTU limit, the image data is sent in two parts, each containing 240 bytes.

#### Image Stream Data Format
The image stream data follows a specific format to represent the grayscale pixel values of the image. Each pixel is represented by a single byte (uint8_t) value ranging from 0 to 255, where 0 represents black and 255 represents white. The data is transmitted row by row, starting from the top-left corner of the image.


#### Data Structure
Total Data Size: 24 (width) x 20 (height) = 480 bytes per frame
Transmission Format: The image data is transmitted in two parts, each containing 240 bytes, due to BLE MTU limitations.

#### Pixel Order
The pixel values are transmitted row by row, starting from the top-left corner of the image and moving horizontally. Each row is transmitted sequentially, and after completing one row, the transmission continues with the next row below it until the entire image is transmitted.

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
