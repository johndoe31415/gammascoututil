#
#	GammaScoutUtil - Tool to communicate with Gamma Scout Geiger counters.
#	Copyright (C) 2011-2011 Johannes Bauer
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

import sys
import time
import serial
from threading import Thread, Condition
from CommunicationError import CommunicationError

class GSConnection(Thread):
	def __init__(self, device, baudrate, debugmode = False):
		Thread.__init__(self)
		self._debugmode = debugmode
		self._conn = serial.Serial(device, baudrate = baudrate, bytesize = 7, parity = "E", stopbits = 1, timeout = 0.1)
		self._quit = False
		self._databuffer = [ ]
		self._linebuffer = ""
		self._bufferhasitems = Condition()
		self._starttime = None
		self._lasttime = None
		self.start()

		# Wait for incoming data
		time.sleep(0.25)

		# And erase from buffer (to skip junk at beginning of connection)
		self._databuffer = [ ]
		self._linebuffer = ""


	def _debug(self, msg):
		if self._debugmode:
			t = time.time()
			if self._starttime is None:
				self._starttime = t
			if self._lasttime is None:
				self._lasttime = t			
			absdifftime = t - self._starttime
			reldifftime = t - self._lasttime
			print("%7.3f %7.3f: %s" % (absdifftime, reldifftime, msg), file = sys.stderr)
			self._lasttime = t
	
	def _nextmsg(self, timeout = 1.0):
		self._debug("Waiting for next message %.2f sec" % (timeout))
		result = None
		timeout_end = time.time() + timeout
		self._bufferhasitems.acquire()
		while (len(self._databuffer) == 0) and (time.time() < timeout_end):
			self._bufferhasitems.wait(timeout_end - time.time())
		if len(self._databuffer) > 0:
			result = self._databuffer[0]
			self._databuffer = self._databuffer[1:]
		self._bufferhasitems.release()
		if result is not None:
			self._debug("# '%s'" % (str(result)))
		else:
			self._debug("# None")
		return result

	def _expectresponse(self, string, timeout = 1.0):
		assert(isinstance(string, str))
		datagram = self._nextmsg(timeout)
		if datagram is None:
			raise CommunicationError("timeout", "Waiting for first response datagram timed out while expecting empty string." % (str(datagram)))
		elif datagram != "":
			raise CommunicationError("unparsable", "Waiting for first response datagram returned '%s' while expecting empty string." % (str(datagram)))
		
		datagram = self._nextmsg(timeout)
		if datagram is None:
			raise CommunicationError("timeout", "Waiting for second response datagram timed out while expecting '%s'." % (str(datagram), string))
		elif datagram != string:
			raise CommunicationError("unparsable", "Waiting for second response datagram returned '%s' while expecting '%s'." % (str(datagram), string))

	def _rxdata(self, data):
		self._linebuffer += data.decode("latin1")
		datagrams = self._linebuffer.split("\r\n")
		self._debug("<- " + str(datagrams))
		self._linebuffer = datagrams[-1]

		if len(datagrams) > 1:
			self._bufferhasitems.acquire()
			for datagram in datagrams[: -1]:
				# These are complete messages
				self._databuffer.append(datagram)
			self._bufferhasitems.notify_all()
			self._bufferhasitems.release()

	def close(self):
		self._quit = True

	def run(self):
		while not self._quit:
			data = self._conn.read(128)
			if len(data) > 0:
				self._rxdata(data)
	
	def _write(self, string):
		self._debug("-> " + string)
		self._conn.write(string.encode("latin1"))

	def _writeslow(self, string):
		self._debug("-> Slow: " + string)
		b = string.encode("latin1")
		for i in range(len(b)):
			n = b[i : i + 1]
			self._conn.write(n)
			time.sleep(0.55)			# 0.4 is actually too fast, 0.5 works (0.55 is some safety margin)

