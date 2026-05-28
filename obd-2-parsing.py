import obd
import logging

logging.basicConfig(level=logging.INFO)

connection = obd.OBD() # auto-connects to USB or RF port
logging.info(connection.status()) # returns an OBDStatus enum

cmd = obd.commands.SPEED # select an OBD command (sensor)

response = connection.query(cmd) # send the command, and parse the response

print(response.value) # returns unit-bearing values thanks to Pint
print(response.value.to("mph")) # user-friendly unit conversions