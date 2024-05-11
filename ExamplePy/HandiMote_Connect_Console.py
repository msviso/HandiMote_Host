import asyncio
from bleak import BleakScanner, BleakClient

# Constants for UUIDs
DEVICE_NAME = "HandiMote"
UUID_GRAY_LEVEL = "f3645566-00b0-4240-ba50-05ca45bf8abc"
UUID_6DOF_SENSOR = "f3645571-00b0-4240-ba50-05ca45bf8abc"
UUID_UART_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UUID_UART_RX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_UART_TX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

async def discover_devices():
    """Scans for BLE devices and filters by the device name."""
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == DEVICE_NAME:
            print(f"Found {DEVICE_NAME}: {device.address}")

async def connect_and_show_notifications(address):
    """Connects to a BLE device by its address and subscribes to notifications."""
    async with BleakClient(address) as client:
        if await client.is_connected():
            print(f"Connected to {address}")

            # Subscribe to Gray Level Image Matrix notifications
            await client.start_notify(UUID_GRAY_LEVEL, notification_handler)
            # Subscribe to 6DoF Motion Sensor Orientation notifications
            await client.start_notify(UUID_6DOF_SENSOR, notification_handler)
            # Subscribe to UART TX notifications
            await client.start_notify(UUID_UART_TX, notification_handler)

            print("Subscribed to notifications. Listening...")
            await asyncio.sleep(30)  # Listen for notifications for 30 seconds

            # Unsubscribe from notifications
            await client.stop_notify(UUID_GRAY_LEVEL)
            await client.stop_notify(UUID_6DOF_SENSOR)
            await client.stop_notify(UUID_UART_TX)
            print("Unsubscribed from notifications.")

def notification_handler(sender, data):
    """Handles incoming notifications from subscribed characteristics."""
    print(f"Notification from {sender}: {data}")

def main():
    while True:
        print("\n1. Search for HandiMote devices")
        print("2. Connect to HandiMote device by address")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            asyncio.run(discover_devices())
        elif choice == "2":
            address = input("Enter device address: ")
            asyncio.run(connect_and_show_notifications(address))
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
