import cv2
import os
import numpy as np
import asyncio
from bleak import BleakClient, BleakScanner
import tkinter as tk
from tkinter import simpledialog
from PIL import Image, ImageTk
import threading
import struct
import quaternion
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from datetime import datetime
from tkinter import scrolledtext

# PyVer = "E0.24.2.0322"  # Not used

resolution_x = 24
resolution_y = 20
scale_factor = 21
image_buff_size = resolution_x * resolution_y
CHARACTERISTIC_UUID = "f3645566-00b0-4240-ba50-05ca45bf8abc"
MOTION_SENSOR_CHARACTERISTIC_UUID = "f3645571-00b0-4240-ba50-05ca45bf8abc"
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHARACTERISTIC_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UART_TX_CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

READ_COMMAND = 0x10
WRITE_WITH_RESPONSE = 0x11
WRITE_WITHOUT_RESPONSE = 0x12

image_data_buffer = []
package_count = 0
save_directory = 'Handimote_Record' 

# Initialize the background subtractor
backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=10, detectShadows=True)

client = None  
is_ble_connected = False
current_image = None
current_image_data = None
last_update_time = 0
update_interval = 0.04

# Create Tkinter window instance
window = tk.Tk()
window.title("MSViso HandiMote Demo Console")

# Create a frame for messages
message_frame = tk.Frame(window)
message_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

# Create a Text widget for the message box
message_box = Text(message_frame, height=4)
message_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

# Create a scrollbar
scrollbar = tk.Scrollbar(message_frame, command=message_box.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
message_box.config(yscrollcommand=scrollbar.set)

left_frame = tk.Frame(window)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

right_frame = tk.Frame(window)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

imu_frame = tk.Frame(window)
imu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
other_frame = tk.Frame(window)
other_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

message_label = tk.Label(window, text="MSVision HandiMote", bg="white", fg="black")
message_label.pack(side=tk.TOP, fill=tk.X)

image_label = tk.Label(window)
image_label.pack()

fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

black = (0, 0, 0)
white = (255, 255, 255)

yaw_label = tk.Label(imu_frame, text="Yaw: 0")
yaw_label.pack()

roll_label = tk.Label(imu_frame, text="Roll: 0")
roll_label.pack()

pitch_label = tk.Label(imu_frame, text="Pitch: 0")
pitch_label.pack()

threshold = 30  

def create_save_directory():
    os.makedirs(save_directory, exist_ok=True)
    print(f"Directory '{save_directory}' is set up.")

def toggle_swap_packages():
    global swap_packages
    swap_packages = not swap_packages
    update_message_box(f"Swap packages: {swap_packages}")

def update_message_box(message):
    message_box.configure(state='normal')  
    message_box.insert(tk.END, message + "\n")  
    message_box.configure(state='disabled')  
    message_box.see(tk.END)  

def capture_and_save_image():
    global current_image
    if current_image is not None:
        current_time = datetime.now().strftime("%H%M%S")
        filename = f"HandiMoteCapture_{current_time}.png"
        filepath = os.path.join(save_directory, filename)
        cv2.imwrite(filepath, current_image)
        print(f"Image saved: {filepath}")
        update_message_box("Image saved: " + filepath)
    else:
        print("No image data to capture.")

async def connect_and_subscribe_to_characteristic(address):
    async with BleakClient(address) as client:
        if client.is_connected:
            update_message_box(f"Connected to the device with address: {address}")  
            print("Connected to the device.")
            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
            await client.start_notify(MOTION_SENSOR_CHARACTERISTIC_UUID, notification_handler)
            await client.start_notify(UART_TX_CHARACTERISTIC_UUID, notification_handler)

            print("Notifications started for motion sensor characteristic.")

            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            finally:
                if client.is_connected:
                    await client.stop_notify(CHARACTERISTIC_UUID)
                    await client.stop_notify(MOTION_SENSOR_CHARACTERISTIC_UUID)
                    await client.stop_notify(UART_TX_CHARACTERISTIC_UUID)
                    await client.disconnect()

async def scan_for_devices(target_device_name):
    devices = await BleakScanner.discover()
    target_devices = [device for device in devices if device.name == target_device_name]
    return target_devices

def parse_motion_sensor_data(data):
    if len(data) == 16:
        qw, qx, qy, qz = struct.unpack('<ffff', data)
        return qw, qx, qy, qz
    else:
        print("Invalid quaternion data length:", len(data))
        return 1, 0, 0, 0  

def process_image_data():
    global image_data_buffer, image_buff_size
    if len(image_data_buffer) == image_buff_size:
        try:
            image_data = image_data_buffer[:image_buff_size]
            image_data_buffer = image_data_buffer[image_buff_size:]
            window.after(0, lambda: update_image(image_data))
        except Exception as e:
            print(f"Error processing data: {e}")

def update_image(image_data):
    image_np = np.array(image_data, dtype=np.uint8).reshape((resolution_y, resolution_x))
    image_testres = np.array(image_data, dtype=np.uint8).reshape((20, 24))
    enlarged_width = resolution_x * scale_factor
    enlarged_height = resolution_y * scale_factor
    image_cv = cv2.resize(image_np, (enlarged_width, enlarged_height), interpolation=cv2.INTER_NEAREST)
    image_cv_bgr = cv2.cvtColor(image_cv, cv2.COLOR_GRAY2BGR)
    global current_image
    current_image = image_cv_bgr
    img = Image.fromarray(current_image)
    imgtk = ImageTk.PhotoImage(image=img)
    image_label.imgtk = imgtk
    image_label.configure(image=imgtk)

def notification_handler(sender, data):
    global last_update_time, image_data_buffer
    current_time = time.time()
    if current_time - last_update_time >= update_interval:
        last_update_time = current_time
        if sender == CHARACTERISTIC_UUID:
            parse_characteristic_data(data)
        elif sender == MOTION_SENSOR_CHARACTERISTIC_UUID:
            parse_motion_sensor_data(data)
        elif sender == UART_TX_CHARACTERISTIC_UUID:
            data_str = data.decode('utf-8')
            print("Received UART data:", data_str)
        else:
            print("Unknown sender:", sender)
        process_image_data()

def parse_characteristic_data(data):
    global image_data_buffer, package_count
    data_len = len(data)
    if data_len > 0:
        package_count += 1
        if package_count % 2 == 0:
            image_data_buffer.extend(data[1:])

def main():
    global client, is_ble_connected
    create_save_directory()

    async def connect_to_device():
        nonlocal is_ble_connected
        device_name = "HandiMote"
        print("Scanning for devices...")
        update_message_box("Scanning for devices...")
        devices = await scan_for_devices(device_name)
        if len(devices) > 0:
            device = devices[0]
            address = device.address
            print(f"Found {device_name} device with address: {address}")
            update_message_box(f"Found {device_name} device with address: {address}")
            try:
                await connect_and_subscribe_to_characteristic(address)
            except Exception as e:
                print(f"Error connecting to device: {e}")
                update_message_box(f"Error connecting to device: {e}")
                is_ble_connected = False
        else:
            print(f"No {device_name} devices found.")
            update_message_box(f"No {device_name} devices found.")
            is_ble_connected = False

    async def run():
        while True:
            await connect_to_device()
            await asyncio.sleep(3)

    loop = asyncio.get_event_loop()
    loop.create_task(run())
    loop.run_forever()

if __name__ == "__main__":
    main()
