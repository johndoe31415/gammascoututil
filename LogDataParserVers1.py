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
from LogDataParser import LogDataParser

class LogDataParserVers1(LogDataParser):
	def __init__(self, data, outputbackend, debugmode = False):
		LogDataParser.__init__(self, data, outputbackend, debugmode)

	def parse(self, length = None):
		serial_number_str = LogDataParser._hexdecify(self._data[0 : 3])
		serial_number = (serial_number_str[2] * 10000) + (serial_number_str[1] * 100) + serial_number_str[0]

		length = (self._data[0x20] << 0) | (self._data[0x21] << 8)

		self._offset = 0x100
		while (self._offset != len(self._data)) and ((length is None) or (self._offset < length)):
			peek = self._peekbyte()
			if (peek & 0xf0) == 0xf0:
				# Control byte
				if peek == 0xfe:
					data = self._nextbytes(6)[1:]
					data = LogDataParser._hexdecify(data)
					(minute, hour, day, month, year) = data
					year += 2000
					self._debug("Set Date: %04d-%02d-%02d %2d:%02d" % (year, month, day, hour, minute))
					self._curdate = datetime.datetime(year, month, day, hour, minute)
				elif peek == 0xff:
					data = self._nextbytes(5)[1:]
					gap = ((data[1] << 8) | data[0]) * 60
					cts = LogDataParser._expcts(data[2 : 4])
					if gap != 0:
						self._debug("Gap: %d:%02d:%02d, Cts: %d, CPM: %.1f" % (gap // 3600, gap % 3600 // 60, gap % 60, cts, cts / gap * 60))
					else:
						self._debug("Zero gap: Cts: %s" % (cts))
					self._gotcounts(gap, cts)
				elif peek == 0xf4:
					self._debug("Interval 1 minute")
					self._nextbytes(1)
					self._interval = 60
				elif peek == 0xf3:
					self._debug("Interval 10 minutes")
					self._nextbytes(1)
					self._interval = 10 * 60
				elif peek == 0xf2:
					self._debug("Interval 1 hour")
					self._nextbytes(1)
					self._interval = 1 * 3600
				elif peek == 0xf1:
					self._debug("Interval 1 day")
					self._nextbytes(1)
					self._interval = 1 * 86400
				elif peek == 0xf0:
					self._debug("Interval 7 days")
					self._nextbytes(1)
					self._interval = 7 * 86400
				else:
					self._debug("Unknown special (0x%x) at offset 0x%x!" % (peek, self._offset))
					sys.exit(1)

			else:
				counts = LogDataParser._expcts(self._nextbytes(2))
				self._gotcounts(self._interval, counts)

if __name__ == "__main__":
	print(LogDataParser._expcts(bytes([ 0x00, 0xaa ])))
	print(LogDataParser._expcts(bytes([ 0x01, 0xbb ])))
	print(LogDataParser._expcts(bytes([ 0x02, 0xcc ])))
	print(LogDataParser._expcts(bytes([ 0x0a, 0xdd ])))
	print(LogDataParser._expcts(bytes([ 0xab, 0xcd ])))

