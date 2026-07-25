from pymodbus.client import ModbusTcpClient

# Connect to device at specific IP
client = ModbusTcpClient("192.168.1.10", port=502)
client.connect()

# Read 10 holding registers starting at address 0
result = client.read_holding_registers(address=0, count=10, slave=1)

if not result.isError():
    print(result.registers)

client.close()