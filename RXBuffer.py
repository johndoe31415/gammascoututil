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

import threading
import time
import logging

from StopWatch import StopWatch

class _CondTimeout():
	def __init__(self, timeout):
		if timeout is not None:
			self._endtime = time.time() + timeout
		else:
			self._endtime = None

	def remaining(self):
		if self._endtime is not None:
			return self._endtime - time.time()
		else:
			# Always a second remaining
			return 1

	def expired(self):
		return self.remaining() < 0

	def next(self):
		timeout = 1.0
		if self._endtime is not None:
			timeout = min(timeout, self.remaining())
		timeout = max(timeout, 0)
		return timeout


class RXBuffer():
	def __init__(self):
		self._buffer = bytearray()
		self._lock = threading.Lock()
		self._cond = threading.Condition(self._lock)
		self._eof = False
		self._log = logging.getLogger("gsu.proto." + self.__class__.__name__)

	def push(self, data):
		assert(isinstance(data, bytes))
		with self._lock:
			self._buffer += data
			self._cond.notify_all()

	def clear(self):
		with self._lock:
			self._buffer = bytearray()
			self._cond.notify_all()

	def _condition_crlf(self, linecnt):
		pattern = bytes([ 13, 10 ])
		if self._buffer.count(pattern) >= linecnt:
			splitbuf = self._buffer.split(pattern)
			result = [ buf.decode("utf-8") for buf in splitbuf[:linecnt] ]
			self._buffer = pattern.join(splitbuf[linecnt:])
			if (len(result) == 1) and (linecnt == 1):
				result = result[0]
			return result

	def _condition_bytecnt(self, bytecnt):
		if len(self._buffer) >= bytecnt:
			result = self._buffer[:bytecnt]
			self._buffer = self._buffer[bytecnt:]
			result = result.decode("utf-8")
			return result

	def waitforcond(self, conditionfn, conditionargs, timeout):
		sw = StopWatch()
		origtimeout = timeout

		result = None
		timeout = _CondTimeout(timeout)
		with self._lock:
			while (not self._eof) and (not timeout.expired()):
				# Count
				result = conditionfn(*conditionargs)
				if result is not None:
					break
				self._cond.wait(timeout.next())

		if result is None:
			self._log.debug("Waiting timed out after %s" % (str(sw)))
		else:
			prc = 100 * (sw.stop() / origtimeout)
			self._log.debug("Waiting successful after %s (%.0f%%)" % (str(sw), prc))
		return result

	def waitforline(self, linecnt, timeout):
		self._log.debug("Waiting for %d line(s) with a timeout of %.1f sec" % (linecnt, timeout))
		return self.waitforcond(self._condition_crlf, (linecnt, ), timeout)

	def waitforbytes(self, bytecnt, timeout):
		print(bytecnt, timeout)
		self._log.debug("Waiting for %d byte(s) with a timeout of %.1f sec" % (bytecnt, timeout))
		return self.waitforcond(self._condition_bytecnt, (bytecnt, ), timeout)

	def seteof(self):
		self._eof = True

	def haveeof(self):
		return self._eof

if __name__ == "__main__":
	buf = RXBuffer()
	buf.push("hallo dat ist ein".encode("utf-8"))
	buf.push(" test\r\nhurra\r\nfsdfsd".encode("utf-8"))
	print(buf.waitforline(1))
	print(buf.waitforline(1))
	print(buf.waitforline(1, 1.0))
	buf.push("\r\nXYZ".encode("utf-8"))
	print(buf.waitforline(1, 1.0))

	print(buf.waitforbytes(1, 1.0))
	print(buf.waitforbytes(1, 1.0))
	print(buf.waitforbytes(1, 1.0))
	print(buf.waitforbytes(1, 1.0))

