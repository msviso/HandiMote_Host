# overview
This document outlines the communication protocol used for UART interconnection. The protocol specifies the format for data exchange between the host and the client.

# Protocol Format
## Introduction
The UART Interconnection Protocol is a communication protocol designed for serial data transmission between a host and a client over UART (Universal Asynchronous Receiver/Transmitter) interface. It is structured to facilitate various types of data exchanges, including general-purpose commands, motion control, and vision data.

![ble link diagram](/Image/BleLinkDiagram.png)


## Key Features
Structured Packet Format: The protocol uses a well-defined packet structure for both transmission (TX) and reception (RX), ensuring reliable data exchange.
Command Types: Supports a range of command types for different purposes, such as general-purpose read/write, motion control, and vision data handling.
Error Checking: Incorporates CRC (Cyclic Redundancy Check) for error detection, enhancing data integrity.

## Packet Structure
#### TX Packet: 
The packet begins with a 2-byte header (0xAA, 0xEE), followed by a command byte that specifies the type of data access (read or write). This is followed by a register code, which identifies the specific data register or command to be accessed. The next byte, referred to as "data length," indicates the number of data bytes that will be included in this packet. The data payload is then provided, followed by a CRC checksum, which uses the CRC-8 algorithm to ensure data integrity. The minimum length of the packet is 6 bytes, ensuring that even the smallest packet includes all necessary information for a valid transaction.


|     Header       |   Command Byte   |  Register Code  |  Data Length    |    Data Payload |     CRC       |
|------------------|------------------|-----------------|-----------------|-----------------|---------------|
| 0xAA       0xEE  |    (1 byte)      |    (1 byte)     |    (1 byte)     |  Up to 241 bytes|   (1 byte)    |



*Explanation of Each Field:*

* Header (2 bytes): Composed of two bytes, 0xAA followed by 0xEE. This header signals the start of a transmission packet, ensuring that the receiving device recognizes the incoming data as a valid command packet.

* Command Byte (1 byte): This byte defines the type of operation that the host wishes to perform on the device. It specifies whether the packet's purpose is to read from or write to a register.

* Register Code (1 byte): Identifies the specific register or command target within the device. This code tells the device exactly which of its registers the command is intended for, facilitating accurate data retrieval or modification.

* Data Length (1 byte): Specifies the length of the Data Payload. Due to BLE MTU limits, the maximum data payload length is 241 bytes in a TX packet. This ensures that the total packet size, including the header, command byte, register code, data length, and CRC, does not exceed 247 bytes.
  
* Data Payload (Variable length): The actual data being sent to the device. The size of this field is variable and is specified by the 'Data Length' field. This could be anything from configuration settings to actual values needed by the device. 

* CRC (1 byte): Contains a CRC-8 checksum of the entire packet (excluding the CRC byte itself). This checksum is used to verify the integrity of the data received, ensuring that no corruption occurred during transmission.

#### RX Packet: 
The response packet initiates with a 2-byte header (0xEE, 0xAA), ensuring consistent recognition at the start of each communication. Following the header, a command byte and a register code are provided. These components serve to clearly identify the original packet or command to which the response corresponds. Next, a byte designated as "data length" indicates the total number of bytes included in the response. The packet is completed with a CRC byte that utilizes the CRC-8 algorithm, verifying the integrity of the data contained within the packet. This format ensures precise and reliable data exchange between the host and the client device.


|     Header       |   Command Byte   |  Register Code  |  Data Length    |    Data Payload |     CRC       |
|------------------|------------------|-----------------|-----------------|-----------------|---------------|
| 0xEE       0xAA  |    (1 byte)      |    (1 byte)     |    (1 byte)     |  Up to 241 bytes|   (1 byte)    |



*Explanation of Each Field:*

* Header (2 bytes): Starts with 0xEE followed by 0xAA to signify the beginning of a response packet.

* Command Byte (1 byte): This byte serves a dual function, indicates the type of operation being acknowledged or responded packet status to by the device.
  
*Normal Operation: In typical scenarios, this byte confirms which specific command the response is addressing, mirroring the command initially sent by the host.*

Error Handling: If an error occurs during the processing of the command or data access, this byte is used to relay error codes. These codes provide insight into the nature of the issue:

    0xFF for general command errors

    0xF0 for CRC errors, indicating data corruption

    0x12 for errors related to improper command usage

    0x13 for discrepancies in expected data lengths

* Register Code (1 byte): Specifies the particular register or command to which this packet is responding.

* Data Length (1 byte): Indicates the number of bytes in the Data Payload for the RX packet. Similar to the TX packet, the maximum length for data in an RX packet is 241 bytes, considering the same BLE MTU restrictions to maintain the total packet size within 247 bytes.

* CRC (1 byte): Provides a CRC-8 checksum of the packet to verify data integrity.

## Command Code Byte
In the BLE communication protocol used between the host and the client device, there are four types of command codes designated to control data interactions. Each command code specifies the action to be performed and dictates the response behavior of the client device.

*Command Code Descriptions* 

- Data Read Command (0x10): This command is used to read data from client registers. Upon receiving this command, the client device will prepare and send the requested data back to the host. The response time may vary depending on the client's processing capabilities or the time required to prepare the data.
- Data Write with Response (0x11): This command is utilized to write data to client registers and expects a response. For example, if the host wants to enable a motion sensor, this command would not only perform the enable action but also require the client to confirm the sensor's enabled status in its response.
- Data Write without Response (0x12): This command allows the host to write data to the client's registers without expecting any response. This is typically used for operations where confirmation of action is not necessary.
- Data Sync Up Command (0x130): This is a reserved command for future use and is not operational at present. It is intended for synchronization purposes between the host and the client.

| Command Code | Description                    | Response Expected          |
|--------------|--------------------------------|----------------------------|
| 0x10         | Data Read Command              | Yes, data from registers   |
| 0x11         | Data Write with Response       | Yes, confirmation of action|
| 0x12         | Data Write without Response    | No response from client    |
| 0x13         | Data Sync Up Command (Reserved)| Reserved for future use    |
| 0xFF         | Error Cmd                       | Transfer Command Error   |

## Data Transmission Order

In our UART communication protocol, data is transferred using Little-Endian byte order. This means that when multiple bytes are used to represent data, the least significant byte (LSB) is transmitted first, followed by the more significant bytes in ascending order of significance. This order applies to all fields in the packet that are larger than one byte.

*Detailed Description of Data Payload*

Data Payload (Variable Length): The data payload consists of the actual data bytes being sent to the device. The size of this field is variable and is determined by the value in the 'Data Length' field, which precedes the payload in the packet structure. The payload can contain a wide variety of data, ranging from configuration settings to sensor readings or command parameters necessary for the operation of the device.


# Register Code

### HandiMote Register code over view, 
| Register | Name            | Description                                          | Length    | Data Type | Reset Value | Writable | Note                                  |
|----------|-----------------|------------------------------------------------------|-----------|-----------|-------------|----------|---------------------------------------|
| 0x00     | MAG_NAME        | HandiMote Magic Name                                 | 2 Bytes   | uint8     | 0x1A2B      | No       |                                       |
| 0x01     | DEV_ID          | Device UUID Number                                   | 12 Bytes  | string    | Device-specific UUID | No       |                                       |
| 0x02     | DEV_TICKCOUNT   | Device Tick Count                                    | 4 Bytes  | uint32     | ----        | No       |                                       |
| 0x03     | DEV_BATC        | Device Battery Capacitor                             | 1 Byte    | uint8     | ----        | No       |                                       |
| 0x04     | DEV_FW_VERSION  | Device Firmware Version                              | 12 Bytes  | string    | ----        | No       |                                       |
| 0x11     | DEV_OPM         | Device Operation Mode                                | 2 Bytes   | uint8     | ----        | Yes      |                                       |
| 0x12     | DEV_PSM_CFG     | Power Save Mode Configure                            | 1 Byte    | uint8     | ----        | Yes      |                                       |
| 0x20     | MOT_ACC_D       | Accelerometer Data X, Y, Z & Timestamp               | 16 Bytes  | Float     | ----        | No       | If ACC not enabled, return 0x00       |
| 0x31     | MOT_CFG         | Motion Parameter configure, Sample Frequency: 100Hz  | 4 Bytes   | uint8     | ----        | Yes      |                                       |
| 0x40     | VISO_STATUS     | Vision Sense Status                                  | 2 Bytes   | uint8     | ----        | No       |                                       |
| 0x51     | VISO_CFG_MOD    | Vision Sensor Parameter Configure                    | 2 Bytes   | uint8     | ----        | Yes      |                                       |
| 0x52     | VISO_PAM_FS     | Vision Sensor Parameter Full-Scale Configure         | 4 Bytes   | uint8     | ----        | Yes      |                                       |
| 0x53     | VISO_PAM_GAN    | Vision Sensor Receiver Gain Set                      | 1 Byte    | uint8     | ----        | Yes      |                                       |

*Note :* Register code detail please refer to [Register Code](Register Code.md)


## CRC-8 Algorithm Example Code
This code snippet provides a straightforward implementation of the CRC-8 checksum algorithm using the polynomial 0x07, which is a common choice for CRC-8 calculations. The function crc8 takes a pointer to an array of data and the length of the array as its arguments. It returns the computed CRC-8 checksum as a uint8_t.


```csharp
   #include <stdint.h>

// Define the polynomial for CRC-8 algorithm
#define CRC8_POLYNOMIAL 0x07

/**
 * Calculate the CRC-8 of the given data.
 * @param data Pointer to the data array.
 * @param length Length of the data array.
 * @return Computed CRC-8 value.
 */
uint8_t crc8(uint8_t *data, size_t length) {
    uint8_t crc = 0x00; // Initial value
    while (length--) {
        crc ^= *data++; // XOR byte into least sig. byte of crc
        
        // Process each bit per byte
        for (int i = 8; i > 0; --i) {
            // Check if the LSB of crc is set
            if (crc & 0x01) {
                crc = (crc >> 1) ^ CRC8_POLYNOMIAL; // Shift right and XOR with polynomial
            } else {
                crc >>= 1; // Just shift right
            }
        }
    }
    return crc; // Final CRC value after processing all bytes and bits
}
```

### Explanation of the Code
**POLYNOMIAL:** Defines the polynomial used for the CRC calculation, which in this case is 
0
𝑥
07
0x07.

**crc8 function:** This function takes an array of data and its length, computes the CRC using the specified polynomial, and returns the CRC value.

**Main Function:** Demonstrates how to use the crc8 function with a sample data array. This part of the code calculates the CRC for the data and prints it.


