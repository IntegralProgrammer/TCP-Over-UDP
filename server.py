#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run with: cpulimit --limit=10 -- python server.py 0.100
"""

import sys
import time
import asyncore
import socket

TX_PAUSE = float(sys.argv[1])

UDP_IP = "127.0.0.1"
UDP_RX_PORT = 9098
UDP_TX_PORT = 9099

TCP_SERVICE_IP = "127.0.0.1"
TCP_SERVICE_PORT = 8000

outputSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

class UDPInput(asyncore.dispatcher):
	def __init__(self, addr, q_out):
		self.output_queue = q_out
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.bind(addr)
	
	def handle_read(self):
		buf = self.recv(4096)
		port = int(buf[0:5])
		new_socket = bool(buf[5] == 'Y')
		if new_socket:
			TCPConnection((TCP_SERVICE_IP, TCP_SERVICE_PORT), port, self.output_queue)
		else:
			data_segment = buf[6:]
			self.output_queue.append((port, data_segment))
		

class TCPConnection(asyncore.dispatcher):
	def __init__(self, addr, fp, q_out):
		self.forwarded_port = fp
		self.outbound_queue = q_out
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect(addr)
	
	def handle_read(self):
		buf = self.recv(1024)
		time.sleep(TX_PAUSE)
		outputSock.sendto(str(self.forwarded_port).zfill(5) + buf, (UDP_IP, UDP_TX_PORT))
		if buf == "":
			self.handle_close()
	
	def handle_write(self):
		msg_idx = -1
		for i in range(len(self.outbound_queue)):
			if self.outbound_queue[i][0] == self.forwarded_port:
				msg_idx = i
				break
		
		if msg_idx != -1:
			sendable_msg = self.outbound_queue[msg_idx][1]
			del self.outbound_queue[i]
			if sendable_msg == "":
				self.handle_close()
			else:
				self.send(sendable_msg)
	
	def handle_close(self):
		self.close()

message_queue = []
server_rx = UDPInput((UDP_IP, UDP_RX_PORT), message_queue)
asyncore.loop()
