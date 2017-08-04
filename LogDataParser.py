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
import datetime

class LogDataParser():
	def __init__(self, data, outputbackend, debugmode = False):
		self._data = data
		self._output = outputbackend
		self._debugmode = debugmode
		self._curdate = None
		self._interval = None

	def _debug(self, text):
		if self._debugmode:
			print(text, file = sys.stderr)

	def _hexdecify(data):
		return [ (10 * ((x & 0xf0) >> 4) + (x & 0x0f))  for x in data ]

	def _peekbyte(self):
		return self._data[self._offset]
	
	def _nextbytes(self, length):
		o = self._offset
		self._offset += length
		return self._data[o : o + length]
	
	def _gotcounts(self, timesecs, counts):
		todate = self._curdate + datetime.timedelta(0, timesecs)
		self._output.newinterval(self._curdate, todate, counts)
		self._debug("%s - %s: %d" % (self._curdate, todate, counts))
		self._curdate = todate

	def parse(self, length = None):
		self._offset = 0
		while (self._offset != len(self._data)) and ((length is None) or (self._offset < length)):
			peek = self._peekbyte()
			if peek == 0xf5:
				# Discard that byte
				self._nextbytes(1)

				peek = self._peekbyte()
				if peek == 0xef:
					data = self._nextbytes(6)[1:]
					data = LogDataParser._hexdecify(data)
					(minute, hour, day, month, year) = data
					year += 2000
					self._debug("Set Date: %04d-%02d-%02d %2d:%02d" % (year, month, day, hour, minute))
					self._curdate = datetime.datetime(year, month, day, hour, minute)
				elif peek == 0xee:
					data = self._nextbytes(5)[1:]
					gap = ((data[1] << 8) | data[0]) * 10
					cts = (data[2] << 8) | data[3]
					self._debug("Gap: %d:%02d:%02d, Cts: %d, CPM: %.1f" % (gap // 3600, gap % 3600 // 60, gap % 60, cts, cts / gap * 60))
					self._gotcounts(gap, cts)
				elif peek == 0x0c:
					self._debug("Interval 10 seconds")
					self._nextbytes(1)
					self._interval = 10
				elif peek == 0x0b:
					self._debug("Interval 30 Seconds")
					self._nextbytes(1)
					self._interval = 30
				elif peek == 0x0a:
					self._debug("Interval 1 minute")
					self._nextbytes(1)
					self._interval = 60
				elif peek == 0x09:
					self._debug("Interval 2 minutes")
					self._nextbytes(1)
					self._interval = 2 * 60
				elif peek == 0x08:
					self._debug("Interval 5 minutes")
					self._nextbytes(1)
					self._interval = 5 * 60
				elif peek == 0x07:
					self._debug("Interval 10 minutes")
					self._nextbytes(1)
					self._interval = 10 * 60
				elif peek == 0x06:
					self._debug("Interval 30 minutes")
					self._nextbytes(1)
					self._interval = 30 * 60
				elif peek == 0x05:
					self._debug("Interval 1 hour")
					self._nextbytes(1)
					self._interval = 1 * 3600
				elif peek == 0x04:
					self._debug("Interval 2 hours")
					self._nextbytes(1)
					self._interval = 2 * 3600
				elif peek == 0x03:
					self._debug("Interval 12 hours")
					self._nextbytes(1)
					self._interval = 12 * 3600
				elif peek == 0x02:
					self._debug("Interval 1 day")
					self._nextbytes(1)
					self._interval = 1 * 86400
				elif peek == 0x01:
					self._debug("Interval 3 days")
					self._nextbytes(1)
					self._interval = 3 * 86400
				elif peek == 0x00:
					self._debug("Interval 7 days")
					self._nextbytes(1)
					self._interval = 7 * 86400
				elif peek == 0xf3:
					self._debug("Unknown command 0xf3")
					self._nextbytes(1)
				elif peek == 0xf4:
					self._debug("Unknown command 0xf4")
					self._nextbytes(1)
				else:
					self._debug("Unknown special (0x%x)!" % (peek))
					sys.exit(1)

			else:
				counts = self._nextbytes(2)
				counts = (counts[0] << 8) | counts[1]
				self._gotcounts(self._interval, counts)

