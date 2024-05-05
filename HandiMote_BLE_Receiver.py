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
import quaternion  # This adds the quaternion dtype to numpy
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from datetime import datetime
from tkinter import Text 
from tkinter import scrolledtext  # For scrollable text area

PyVer = "E0.24.2.0322"

image_data_buffer = []
resolution_x = 24
resolution_y = 20
scale_factor = 21
image_buff_size = resolution_x * resolution_y
package_count = 0
save_directory = 'Handimote_Record'  # Correct directory name
CHARACTERISTIC_UUID = "f3645566-00b0-4240-ba50-05ca45bf8abc"
MOTION_SENSOR_CHARACTERISTIC_UUID = "f3645571-00b0-4240-ba50-05ca45bf8abc"
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_CHARACTERISTIC_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # RX for the device to receive data
UART_TX_CHARACTERISTIC_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # TX for the device to send data

READ_COMMAND = 0x10
WRITE_WITH_RESPONSE = 0x11
WRITE_WITHOUT_RESPONSE = 0x12

# Initialize variables
package_count = 0
first_package_received = False
swap_packages = False
raw_image_data = None

script_dir = os.path.dirname(os.path.abspath(__file__))

# Initialize the background subtractor
backSub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=10, detectShadows=True)

client = None  # 定義一個全局變量用於存儲BLE客戶端實例
is_ble_connected = False
current_image = None
capture_count = 0
current_image_data = None
raw_capture_count = 0


last_update_time = 0
update_interval = 0.04 # 更新间隔（秒） 

# 创建Tkinter窗口实例
window = tk.Tk()
window.title("MSViso HandiMote Demo Console")

message_frame = tk.Frame(window)
message_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

# 创建一个Text小部件作为消息框
message_box = Text(message_frame, height=4)
message_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

# 创建一个滚动条
scrollbar = tk.Scrollbar(message_frame, command=message_box.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
message_box.config(yscrollcommand=scrollbar.set)

# In your window setup code     // reserved for the gestrue ouptut console used
#console_frame = tk.Frame(window)
#console_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

#console_output = Text(console_frame, state='disabled')  # Initially disabled for writing
#console_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 创建Frame
left_frame = tk.Frame(window)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

right_frame = tk.Frame(window)
right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# 创建两个Frame，一个用于IMU数据，一个用于其他控件
imu_frame = tk.Frame(window)
imu_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
other_frame = tk.Frame(window)
other_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

message_label = tk.Label(window, text="MSVison HandiMote", bg="white", fg="black")
message_label.pack(side=tk.TOP, fill=tk.X)

message_label = tk.Label(window, text=PyVer, bg="white", fg="black")
message_label.pack(side=tk.TOP, fill=tk.X)


image_label = tk.Label(window)
image_label.pack()

fig, ax = plt.subplots(subplot_kw={'projection': '3d'})
canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

# 设置颜色
black = (0, 0, 0)
white = (255, 255, 255)

# 用于模拟传感器数据的变量
roll, pitch, yaw = 0, 0, 0

# 在IMU Frame中创建标签
yaw_label = tk.Label(imu_frame, text="Yaw: 0")
yaw_label.pack()

roll_label = tk.Label(imu_frame, text="Roll: 0")
roll_label.pack()

pitch_label = tk.Label(imu_frame, text="Pitch: 0")
pitch_label.pack()

threshold = 30  # 閾值，需要根據實際情況調整


def create_gui():
    # Create the main window
    window = tk.Tk()
    window.title("BLE UART Communication")

    # Create a frame for input and send button
    input_frame = tk.Frame(window)
    input_frame.pack(padx=10, pady=10)

    # Text entry widget
    text_entry = tk.Entry(input_frame, width=50)
    text_entry.pack(side=tk.LEFT, padx=(0, 10))

    # Send button
    send_button = tk.Button(input_frame, text="Send", command=lambda: send_data(text_entry.get()))
    send_button.pack(side=tk.LEFT)

    # Scrollable text area for messages
    message_box = scrolledtext.ScrolledText(window, height=15, width=60)
    message_box.pack(padx=10, pady=10)
    message_box.config(state='disabled')  # Disable editing of received messages

    return window, text_entry, message_box

def send_data(message):
    # Implement the function to send data over BLE here
    print("Sending:", message)
    # For demonstration, let's echo the message to the message box
    display_message(message)

def display_message(message):
    message_box.config(state='normal')
    message_box.insert(tk.END, message + "\n")
    message_box.yview(tk.END)
    message_box.config(state='disabled')


def update_message_box(message):
    """更新消息框中的消息。"""
    message_box.configure(state='normal')  # 启用编辑
    message_box.insert(tk.END, message + "\n")  # 在末尾插入新消息
    message_box.configure(state='disabled')  # 禁用编辑
    message_box.see(tk.END)  # 自动滚动到最新消息


def create_save_directory():
    save_directory = 'Handimote_Record'
    os.makedirs(save_directory, exist_ok=True)
    print(f"Directory '{save_directory}' is set up.")

def capture_and_save_bin():
    global raw_image_data
    if raw_image_data is not None:
        # Convert the list of integers to bytes
        image_bytes = bytes(raw_image_data)

        # Get current time and format it as hhmmss
        current_time = datetime.now().strftime("%H%M%S")

        # Define file path with time-based filename
        file_path = os.path.join(save_directory, f'captured_{current_time}.bin')

        # Write data to file
        with open(file_path, 'wb') as file:
            file.write(image_bytes)
        print(f"Captured data saved as {file_path}")
       
    else:
        print("No raw image data to capture.")


def toggle_swap_packages():
    global swap_packages
    swap_packages = not swap_packages
    #print(f"Swap packages: {swap_packages}")
    update_message_box(f"Swap packages: {swap_packages}")

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
            update_message_box(f"Connected to the device with address: {address}")  # Add this line to show the address
            print("Connected to the device.")
            await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
            await client.start_notify(MOTION_SENSOR_CHARACTERISTIC_UUID, notification_handler)
            await client.start_notify(UART_TX_CHARACTERISTIC_UUID, notification_handler)

            print("Notifications started for motion sensor characteristic.")

            # Read command example
            read_packet = read_data(0x00)
            await send_uart_command(client, read_packet)

            read_packet = read_data(0x01)
            await send_uart_command(client, read_packet)

            read_packet = read_data(0x02)
            await send_uart_command(client, read_packet)

            read_packet = read_data(0x02)
            await send_uart_command(client, read_packet)

            read_packet = read_data(0x53)
            await send_uart_command(client, read_packet)


            try:
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                # Properly handle the cancellation
                pass
            finally:
                # Gracefully stop notifications if still connected
                if client.is_connected:
                    await client.stop_notify(CHARACTERISTIC_UUID)
                    await client.stop_notify(MOTION_SENSOR_CHARACTERISTIC_UUID)
                    await client.stop_notify(UART_TX_CHARACTERISTIC_UUID)
                    await client.disconnect()

async def scan_for_devices(target_device_name):
    """扫描特定名称的BLE设备"""
    devices = await BleakScanner.discover()
    target_devices = [device for device in devices if device.name == target_device_name]
    return target_devices


def parse_motion_sensor_data(data):
    if len(data) == 16:
        # Unpack the data into four float values for the quaternion (qw, qx, qy, qz)
        qw, qx, qy, qz = struct.unpack('<ffff', data)
        return qw, qx, qy, qz
    else:
        print("Invalid quaternion data length:", len(data))
        return 1, 0, 0, 0  # Return a default quaternion (no rotation)

def reset_view():
    ax.view_init(elev=30, azim=-60)  # Reset the view to default values
    canvas.draw()

def select_device(target_device_name):

    devices = asyncio.run(scan_for_devices(target_device_name))
    devices_dict = {device.name: device for device in devices}
    device_names = list(devices_dict.keys())

    if not device_names:
        print(f"Can't Found The Device Name :'{target_device_name}'BLE Devices")
        return None

    selected_device_name = simpledialog.askstring("Select Device", "Available devices:\n" + "\n".join(device_names))
    if not selected_device_name:
        print("No Device Select")
        return None

    selected_device = devices_dict.get(selected_device_name, None)
    return selected_device.address if selected_device else None


def update_imu_labels(roll, pitch, yaw):
    # 更新标签文本
    yaw_label.config(text=f"Yaw: {yaw:.2f}")
    roll_label.config(text=f"Roll: {roll:.2f}")
    pitch_label.config(text=f"Pitch: {pitch:.2f}")


def update_image(image_data):
    """Update the displayed image with new data."""
    image_np = np.array(image_data, dtype=np.uint8).reshape((resolution_y, resolution_x))
    image_testres = np.array(image_data, dtype=np.uint8).reshape((20, 24))
    
    #for index, byte in enumerate(image_np.flatten()):
    #    print(f"memory data [{index}] = 0x{byte:02x}")
    
    # Enlarge the image
    enlarged_width = resolution_x * scale_factor
    enlarged_height = resolution_y * scale_factor
    image_cv = cv2.resize(image_np, (enlarged_width, enlarged_height), interpolation=cv2.INTER_NEAREST)
    image_test = cv2.resize(image_testres, (enlarged_width, enlarged_height), interpolation=cv2.INTER_NEAREST)



    cv2.imshow("Real-time Image", image_test)
    cv2.waitKey(1)  # Use cv2.waitKey(1) to allow for UI events
    # Convert to PIL Image for display
    image_pil = Image.fromarray(image_cv)
    imgtk = ImageTk.PhotoImage(image=image_pil)
    image_label.imgtk = imgtk
    image_label.configure(image=imgtk)

def process_image_data():
    global image_data_buffer, image_buff_size, current_image
    # Check if the buffer size matches the expected image size
    if len(image_data_buffer) == image_buff_size:
        try:
            image_data = image_data_buffer[:image_buff_size]
            # Reset buffer for next image
            image_data_buffer = image_data_buffer[image_buff_size:]
            
            # Update the current_image for saving or further processing
            #current_image = np.array(image_data, dtype=np.uint8).reshape((resolution_x, resolution_y))
            #current_image = cv2.resize(current_image, (resolution_x * scale_factor, resolution_y * scale_factor), interpolation=cv2.INTER_LINEAR)
            
            # Update the displayed image
            window.after(0, lambda: update_image(image_data))
        except Exception as e:
            print(f"Error processing data: {e}")


def update_imu_visualization(quat):
    global last_update_time
    current_time = time.time()
    if np.isclose(quat.norm(), 0):
        #print("Quaternion has zero norm, skipping rotation.")
        return

    if current_time - last_update_time > update_interval:
        #draw_cube(ax, quat)  # Or draw_flying_plant(ax, quat) if you're using the flying plant visualization
        draw_flying_plant(ax, quat)
        last_update_time = current_time

def read_data(register_code):
    return build_uart_packet(READ_COMMAND, register_code, b'')

def write_with_response(register_code, data):
    return build_uart_packet(WRITE_WITH_RESPONSE, register_code, data)

def write_without_response(register_code, data):
    return build_uart_packet(WRITE_WITHOUT_RESPONSE, register_code, data)


def build_uart_packet(command_code, register_code, data):
    data_length = len(data) + 6  # command_code, register_code, CRC
    packet = bytes([0xAA, 0xEE, command_code, register_code, data_length]) + data
    crc = calculate_crc8(packet)  

    return packet + bytes([crc])

def calculate_crc8(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x07  # Polynomial for CRC-8
            else:
                crc <<= 1
            crc &= 0xFF  # Ensure CRC remains within 8 bits
    return crc


async def send_uart_command(client, packet):
    await client.write_gatt_char(UART_RX_CHARACTERISTIC_UUID, packet)
    print(f"Sent package: {packet.hex()}")

def notification_handler(sender, data):
    global image_data_buffer, package_count, first_package_received, swap_packages, current_image

    if sender.uuid == CHARACTERISTIC_UUID:
        # Handle image data
        package_count += 1
        
        if package_count == 1:
            if len(data) == 240:  # Assuming first package is always 240 bytes
                first_package_received = True
                image_data_buffer = list(data)
            else:
                first_package_received = False
                package_count = 0  # Reset package count if data does not match expected size

        elif package_count == 2:
            if first_package_received:
                if swap_packages:
                    image_data_buffer = list(data) + image_data_buffer
                else:
                    image_data_buffer.extend(list(data))
                process_image_data()  # Process image data if complete
            package_count = 0  # Reset package count after processing second package

    elif sender.uuid == MOTION_SENSOR_CHARACTERISTIC_UUID:
        # Process motion sensor data
        process_motion_sensor_data(data)

    elif sender.uuid == UART_TX_CHARACTERISTIC_UUID:
        # Handle UART data (e.g., commands or messages)
        process_uart_data(sender, data)

def process_motion_sensor_data(data):
    try:
        qw, qx, qy, qz = parse_motion_sensor_data(data)
        window.after(0, lambda: update_imu_visualization(np.quaternion(qw, qx, qy, qz)))
    except Exception as e:
        print(f"Error processing motion sensor data: {e}")

def process_uart_data(sender, data):
    
        print(f"Received data from {sender}: {data.hex()}")
        parsed_data = parse_response(data)
        if parsed_data:
            process_received_data(parsed_data)

def parse_response(data):
    # Check minimum length (header + command + register + length + CRC)
    if len(data) < 6:
        print("Data is too short to be valid.")
        return None

    # Check header
    if data[0:2] != b'\xEE\xAA':
        print("Invalid header")
        return None

    # Extract parts of the message
    command_code = data[2]
    register_code = data[3]
    data_length = data[4]
    expected_crc = data[-1]  # Last byte is CRC

    # Verify the length
    if data_length != len(data):
        print(f"Data length mismatch: expected {data_length}, got {len(data)}")
        return None

    # Extract payload
    payload = data[5:-1]  # From after length to before CRC

    # Calculate CRC
    calculated_crc = calculate_crc8(data[:-1])  # Calculate CRC excluding the actual CRC byte
    if calculated_crc != expected_crc:
        print(f"CRC mismatch: expected {expected_crc}, got {calculated_crc}")
        return None

    print("Data packet is valid.")
    return {
        'command_code': command_code,
        'register_code': register_code,
        'payload': payload,
        'data_length' : data_length
    }

def process_received_data(parsed_data):
    # Process the parsed data
    print(f"Command Code: {parsed_data['command_code']}")
    print(f"Register Code: {parsed_data['register_code']}")
    print(f"Payload: {parsed_data['payload'].hex()}")
    print(f"data_length: {parsed_data['data_length']}")

def run_asyncio_loop(loop, device_address):
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(connect_and_subscribe_to_characteristic(device_address))
    except asyncio.CancelledError:
        # Handle cancellations during the loop shutdown
        pass
    except RuntimeError as e:
        # Handle runtime error if the loop is stopped
        print(f"Runtime error in asyncio loop: {e}")
    finally:
        loop.close()


# Then, modify your `on_close_button_clicked` function to stop the loop safely

def draw_cube(ax, quat):
    # Define the vertices of a unit cube
    vertices = np.array([[-0.5, -0.5, -0.5],
                         [0.5, -0.5, -0.5],
                         [0.5, 0.5, -0.5],
                         [-0.5, 0.5, -0.5],
                         [-0.5, -0.5, 0.5],
                         [0.5, -0.5, 0.5],
                         [0.5, 0.5, 0.5],
                         [-0.5, 0.5, 0.5]])

    # Define the faces of the cube
    faces = [[vertices[i] for i in [0, 1, 2, 3]],
             [vertices[i] for i in [4, 5, 6, 7]],
             [vertices[i] for i in [0, 3, 7, 4]],
             [vertices[i] for i in [1, 2, 6, 5]],
             [vertices[i] for i in [0, 1, 5, 4]],
             [vertices[i] for i in [2, 3, 7, 6]]]

    # Rotate the vertices by the quaternion
    rotated_vertices = [quaternion.rotate_vectors(quat, face) for face in faces]

    # Create a 3D polygon collection for the rotated cube
    cube = Poly3DCollection(rotated_vertices, facecolors='cyan', linewidths=1, edgecolors='r', alpha=.25)

    ax.clear()
    ax.add_collection3d(cube)
    ax.set_axis_off()
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])

    canvas.draw()


def draw_flying_plant(ax, quat):
    # Define the vertices of a pyramid
    vertices = np.array([[0, 0, 0.5],  # Top vertex
                         [-0.5, -0.5, -0.5],  # Base vertices
                         [0.5, -0.5, -0.5],
                         [0.5, 0.5, -0.5],
                         [-0.5, 0.5, -0.5]])

    # Define the faces of the pyramid
    faces = [[vertices[i] for i in [0, 1, 2]],
             [vertices[i] for i in [0, 2, 3]],
             [vertices[i] for i in [0, 3, 4]],
             [vertices[i] for i in [0, 4, 1]],
             [vertices[i] for i in [1, 2, 3, 4]]]  # Base

    # Rotate the vertices by the quaternion
    rotated_faces = [quaternion.rotate_vectors(quat, face) for face in faces]

    # Create a 3D polygon collection for the rotated pyramid
    plant = Poly3DCollection(rotated_faces, facecolors='green', linewidths=1, edgecolors='r', alpha=.25)

    ax.clear()
    ax.add_collection3d(plant)
    ax.set_axis_off()
    ax.set_xlim([-1, 1])
    ax.set_ylim([-1, 1])
    ax.set_zlim([-1, 1])

    canvas.draw()


async def disconnect_client():
    global client
    if client and client.is_connected:
        await client.disconnect()

def on_close_button_clicked():
    global asyncio_thread, loop, client

    if client and client.is_connected:
        # 安全地處理客戶端斷開連接
        asyncio.run_coroutine_threadsafe(disconnect_client(), loop)
    
    # 等待所有異步任務完成
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass

    # 關閉事件循環
    loop.call_soon_threadsafe(loop.stop)

    # 確保後台線程結束
    if asyncio_thread.is_alive():
        asyncio_thread.join()

    # 正確關閉 Tkinter 窗口
    window.quit()
    window.destroy()


async def run_select_device():
    devices = await scan_for_devices()
    device_address = select_device(devices)
    if device_address:
        # 连接设备等逻辑
        pass
    else:
        print("No device selected or found.")

def main():
    global window, text_entry, message_box
    window, text_entry, message_box = create_gui()

    # Start BLE operations in a separate thread if needed
    ble_thread = threading.Thread(target=ble_operations)
    ble_thread.start()

    window.mainloop()  # Start the GUI event loop

    # Wait for the BLE thread to finish (if necessary)
    ble_thread.join()

# Main Program Execution
if __name__ == "__main__":
    TARGET_DEVICE_NAME = "HandiMote"
    DEVICE_ADDRESS = select_device(TARGET_DEVICE_NAME)
    create_save_directory()
    current_directory = os.getcwd()
    print(f"Current working directory: {current_directory}")
    
    if DEVICE_ADDRESS:
        loop = asyncio.new_event_loop()
        asyncio_thread = threading.Thread(target=run_asyncio_loop, args=(loop, DEVICE_ADDRESS))
        asyncio_thread.start()

        close_button_frame = tk.Frame(window)
        close_button_frame.pack(anchor=tk.E)
        # 在Frame中創建按鈕和描述
        close_button = tk.Button(close_button_frame, text="Close Demo", command=on_close_button_clicked)
        close_button.pack(side=tk.LEFT)
        close_button_description = tk.Label(close_button_frame, text="Close console and disconnect with BLE")
        close_button_description.pack(side=tk.LEFT)

        capture_button_frame = tk.Frame(window)
        capture_button_frame.pack(anchor=tk.E)
        capture_button = tk.Button(capture_button_frame, text="Capture Image", command=capture_and_save_image)
        capture_button.pack(side=tk.LEFT)
        capture_button_description = tk.Label(capture_button_frame, text="Capture the Image as PNG")
        capture_button_description.pack(side=tk.LEFT)

        swap_button_frame = tk.Frame(window)
        swap_button_frame.pack(anchor=tk.E)
        swap_button = tk.Button(swap_button_frame, text="Swap Packages", command=toggle_swap_packages)
        swap_button.pack(side=tk.LEFT)
        swap_button_description = tk.Label(swap_button_frame, text="press it when the image is Break")
        swap_button_description.pack(side=tk.LEFT)

        window.protocol("WM_DELETE_WINDOW", on_close_button_clicked)
        window.mainloop()


        if asyncio_thread.is_alive():
            asyncio_thread.join()

        main()
    else:
        print("No device selected or found.")


