#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run with: cpulimit --limit=10 -- python client.py 0.100
"""

import sys
import time
import asyncore
import socket

TX_PAUSE = float(sys.argv[1])

class ProxyServer(asyncore.dispatcher):
	def __init__(self, addr, q_in, q_out):
		self.inbound_queue = q_in
		self.outbound_queue = q_out
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind(addr)
		self.listen(100)
	
	def handle_accept(self):
		client_conn, client_info = self.accept()
		self.outbound_queue.append((client_info[1], "", True))
		ProxyConnection(client_conn, client_info, self.inbound_queue, self.outbound_queue)
		#print "New connection from {} started...".format(client_info) #Uncomment to debug


class ProxyConnection(asyncore.dispatcher):
	def __init__(self, conn, info, q_in, q_out):
		self.this_peer = info
		self.inbound_queue = q_in
		self.outbound_queue = q_out
		asyncore.dispatcher.__init__(self, conn)
	
	def handle_read(self):
		buf = self.recv(1024)
		self.outbound_queue.append((self.this_peer[1], buf, False))
		#print "Connection {}, received {}".format(self.this_peer, buf)
		if buf == "":
			self.handle_close()
	
	def handle_write(self):
		msg_idx = -1
		for i in range(len(self.inbound_queue)):
			if self.inbound_queue[i][0] == self.this_peer[1]:
				msg_idx = i
				break
		
		if msg_idx != -1:
			sendable_msg = self.inbound_queue[msg_idx][1]
			del self.inbound_queue[i]
			if len(sendable_msg) > 0:
				self.send(sendable_msg)
			else:
				self.handle_close()
	
	def handle_close(self):
		#print "Connection {} has closed.".format(self.this_peer) #Uncomment to debug
		self.close()


class UDPCollectorTunnel(asyncore.dispatcher):
	def __init__(self, addr, q_in):
		self.inbound_queue = q_in
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.bind(addr)
	
	def handle_read(self):
		buf = self.recv(2048)
		rx = buf[0:5]
		msg = buf[5:]
		self.inbound_queue.append((int(rx), msg))
		#print "UDP Tunnel will forward {} to client {}.".format(msg, rx) #Uncomment to debug


class UDPEmitterTunnel(asyncore.dispatcher):
	def __init__(self, addr, q_out):
		self.endpoint_addr = addr
		self.outbound_queue = q_out
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
	
	def handle_write(self):
		if len(self.outbound_queue) > 0:
			record = self.outbound_queue[0]
			#print "UDP Tunnel passing {}...".format(record) #Uncomment to debug
			flag_open = "N"
			if record[2] == True:
				flag_open = "Y"
			time.sleep(TX_PAUSE)
			self.sendto(str(record[0]) + flag_open + str(record[1]), self.endpoint_addr)
			del self.outbound_queue[0]


to_tcp_queue = []
to_udp_queue = []

udp_collector = UDPCollectorTunnel(('127.0.0.1', 9099), to_tcp_queue)
udp_emitter = UDPEmitterTunnel(('127.0.0.1', 9098), to_udp_queue)

tunnel_entrypoint = ProxyServer(('127.0.0.1', 5555), to_tcp_queue, to_udp_queue)
asyncore.loop()
