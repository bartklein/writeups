from pymodbus.client import ModbusTcpClient

# --- Configuration ---
IP = "192.168.x.x"       # Replace with the actual IP
PORT = 5020
UNIT_ID = 1

# --- Connect ---
client = ModbusTcpClient(IP, port=PORT)
client.connect()

# Read enough registers to capture the full flag (adjust if needed)
result = client.read_holding_registers(address=0, count=15, slave=UNIT_ID)

if result.isError():
    print("Error:", result)
else:
    raw = result.registers
    print("Raw registers:", raw)

    # Build flag: each register holds one ASCII character in its low byte
    flag = ""
    for reg in raw:
        char_code = reg & 0xFF          # Extract low byte
        if char_code == 0:              # Stop at null terminator
            break
        char = chr(char_code)
        flag += char
        if char == '}':                 # Stop after closing brace
            break

    print("Flag:", flag)

client.close()