import asyncio
import subprocess
import drawio_functions as Drawio
import xml.etree.ElementTree as ET
import re
import shutil
from pysnmp.hlapi import *

#load config file
config = {}

#snmp values for 1.3.6.1.2.1.2.2.1.8 - ifOperStatus
online = 1
offline = 2

with open('config.txt', 'r') as f:
	for line in f:
		# Split the line into a key and a value
		key, value = line.strip().split('=')
		# Store the key-value pair in the dictionary
		config[key] = value

class Interface:
	def __init__(self, int_id, name, status):
		self.int_id = int_id
		self.name = name
		self.status = status


class Device:
	def __init__(self, ip, name):
		self.ip = ip
		self.name = name
		self.status = 0
		self.neighbors = []
		self.interfaces = []

		self.update_interfaces()


	async def ping(self):
		command = f"ping /n 3 /a {self.ip}"
		process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		stdout, stderr = process.communicate()
		return process.returncode == 0

	async def update_status(self):
		is_online = await self.ping()
		self.status = is_online

		if is_online:
			print(f"{self.ip}: {self.name} - Online")
		else:
			print(f"{self.ip}: {self.name} - Offline")

	def get_snmp_data(self, oid):
		table = {}
		iterator = nextCmd(SnmpEngine(),
			CommunityData(config['community_string']),
			UdpTransportTarget((self.ip, 161)),
			ContextData(),
			ObjectType(ObjectIdentity(oid)),
			lexicographicMode = False)

		for errorIndication, errorStatus, errorIndex, var_binds in iterator:
			for var_bind in var_binds:
				#print(' = '.join([x.prettyPrint() for x in var_bind]))
				oid, value = var_bind
				interface_index = oid.prettyPrint().split('.')[-1]
				table[interface_index] = value.prettyPrint()
		return table

	def update_interfaces(self):
		updated_interfaces = []
		interface_statuses = self.get_snmp_data('1.3.6.1.2.1.2.2.1.8')
		interface_descs = self.get_snmp_data('1.3.6.1.2.1.2.2.1.2')
		for interface_id, interface_name in interface_descs.items():
			interface_status = interface_statuses[interface_id]
			the_interface = Interface(interface_id, interface_name, interface_status)
			updated_interfaces.append(the_interface)
		self.interfaces = updated_interfaces
			
		print("---------------------")
		print(self.interfaces)
		print("---------------------")
		for interface in self.interfaces:
			print(interface.name, interface.status)



def get_device_list_from_cells(data):
	device_list = []
	cells = []
	# Parse the XML file
	root = ET.fromstring(data)

	# Iterate through all mxCell elements
	for mxcell in root.findall('.//mxCell'):
		print(mxcell.attrib)
		# Check if the mxCell has a value attribute
		if 'value' in mxcell.attrib:
			# Print the value of the mxCell
			cells.append(mxcell)

	for cell in cells:
		print(cell.attrib['value'])
		cellvalue = cell.attrib['value']
		pattern = r"<br>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
		match = re.search(pattern, cellvalue)
		if match:
			name, ip_address = cellvalue.split("<br>")
			device_list.append(Device(ip_address, name))
	return device_list

def update_cells(data, devices):
	online_style = "rounded=0;whiteSpace=wrap;html=1;fillColor=green;"
	offline_style = "rounded=0;whiteSpace=wrap;html=1;fillColor=red;"
	root = ET.fromstring(data)

	for mxcell in root.findall('.//mxCell'):
		for device in devices:
			if 'value' in mxcell.attrib and f"{device.name}<br>{device.ip}" in mxcell.attrib['value']:
				if device.status == 1:
					mxcell.attrib['style'] = online_style
				else:
					mxcell.attrib['style'] = offline_style
				print(mxcell.attrib['style'])
	newdata = ET.tostring(root).decode('utf-8')
	with open("temp.drawio", 'w') as file:
		# Read the contents of the file
		file.write(newdata)

	command = f"draw.io\\draw.io.exe --export temp.drawio --format svg --uncompressed --output tempsvg.svg"
	process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	stdout, stderr = process.communicate()
	output_file_corrected = config['output_file']
	shutil.move(r"tempsvg.svg", f"{output_file_corrected}")
	return process.returncode == 0


	


async def main():
	drawio_data = Drawio.DrawioDecoder(config['input_file'])
	decoded_drawio_data = drawio_data.decoded_data
	devices = get_device_list_from_cells(decoded_drawio_data)

	while True:
		# Start a task to update the status of each Device
		tasks = [asyncio.create_task(device.update_status()) for device in devices]

		# Wait for all tasks to complete
		await asyncio.gather(*tasks)

		# Sleep for 5 seconds before updating again
		await asyncio.sleep(5)
		for device in devices:
			device.update_interfaces()
		update_cells(decoded_drawio_data, devices)


asyncio.run(main())