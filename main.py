import asyncio
import subprocess
import sqlite3
import drawio_functions as Drawio
import xml.etree.ElementTree as ET
import re

class Device:
	def __init__(self, ip, name):
		self.ip = ip
		self.name = name
		self.status = 0
		self.neighbors = []

		# Connect to the database and create a table if it doesn't exist
		self.conn = sqlite3.connect("devices.db")
		c = self.conn.cursor()
		c.execute(
			"CREATE TABLE IF NOT EXISTS devices (ip text, name text, online integer)"
		)
		# initialize the device as offline
		c.execute(
			"INSERT OR REPLACE INTO devices VALUES (?, ?, ?)", (self.ip, self.name, 0)
		)
		self.conn.commit()

	async def ping(self):
		command = f"ping /n 3 /a {self.ip}"
		process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
		stdout, stderr = process.communicate()
		return process.returncode == 0

	async def update_status(self):
		is_online = await self.ping()
		self.status = is_online

		# Update the online status in the database
		c = self.conn.cursor()
		c.execute(
			"UPDATE devices SET online = ? WHERE ip = ? AND name = ?",
			(is_online, self.ip, self.name),
		)
		self.conn.commit()

		if is_online:
			print(f"{self.ip}: {self.name} - Online")
		else:
			print(f"{self.ip}: {self.name} - Offline")






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

	command = f"draw.io\\draw.io.exe --export temp.drawio --format svg --uncompressed --output testing.svg"
	process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	stdout, stderr = process.communicate()
	return process.returncode == 0


	


async def main():
	drawio_data = Drawio.DrawioDecoder("testdiagram.drawio")
	decoded_drawio_data = drawio_data.decoded_data
	devices = get_device_list_from_cells(decoded_drawio_data)

	while True:
		# Start a task to update the status of each Device
		tasks = [asyncio.create_task(device.update_status()) for device in devices]

		# Wait for all tasks to complete
		await asyncio.gather(*tasks)

		# Sleep for 5 seconds before updating again
		await asyncio.sleep(5)
		update_cells(decoded_drawio_data, devices)


asyncio.run(main())