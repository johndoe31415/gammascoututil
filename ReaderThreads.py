#
#	GammaScoutUtil - Tool to communicate with Gamma Scout Geiger counters.
#	Copyright (C) 2011-2013 Johannes Bauer
#
#	This file is part of GammaScoutUtil.
#
#	GammaScoutUtil is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	GammaScoutUtil is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with GammaScoutUtil; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>
#

import socket
import threading
import logging
import select

class SocketReaderThread(threading.Thread):
	def __init__(self, socket, rxcallback, closecallback = None):
		threading.Thread.__init__(self)
		self._log = logging.getLogger("gsu.traffic." + self.__class__.__name__)
		self._socket = socket
		self._rxcallback = rxcallback
		self._closecallback = closecallback
		self._quit = False

	def _rxdata(self, data):
		self._log.debug("RX %d <- %s" % (len(data), str(data)[1:]))
		self._rxcallback(data)

	def run(self):
		while not self._quit:
			data = self._socket.recv(1024)
			if len(data) == 0:
				break
			self._rxdata(data)
		if self._closecallback is not None:
			self._closecallback()

	def close(self):
		if self._quit == False:
			self._quit = True
			self._socket.shutdown(socket.SHUT_RDWR)
			self._socket.close()


class RS232ReaderThread(threading.Thread):
	def __init__(self, conn, rxcallback, closecallback = None):
		threading.Thread.__init__(self)
		self._log = logging.getLogger("gsu.traffic." + self.__class__.__name__)
		self._conn = conn
		self._rxcallback = rxcallback
		self._closecallback = closecallback
		self._quit = False

	def _rxdata(self, data):
		self._log.debug("RX %d <- %s" % (len(data), str(data)[1:]))
		self._rxcallback(data)

	def run(self):
		while not self._quit:
			try:
				data = self._conn.read(128)
			except select.error as e:
				self._log.debug("Read returned from kernel with error: [%d] %s" % (len(e.args), str(e)))
				continue
			if len(data) == 0:
				continue
			self._rxdata(data)
		if self._closecallback is not None:
			self._closecallback()

	def close(self):
		if self._quit == False:
			self._quit = True
			self._conn.close()

