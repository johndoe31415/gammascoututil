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

class LogDataParserVers2(LogDataParser):
	def __init__(self, data, outputbackend):
		LogDataParser.__init__(self, data, outputbackend)

	def parse(self, length = None):
		self._offset = 0
		self._overflow = False

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
					self._log.debug("0x%x: Set Date: %04d-%02d-%02d %2d:%02d" % (self._offset, year, month, day, hour, minute))
					self._curdate = datetime.datetime(year, month, day, hour, minute)
				elif peek == 0xee:
					data = self._nextbytes(5)[1:]
					gap = ((data[1] << 8) | data[0]) * 10
					cts = self._expcts(data[2 : 4])
					self._log.debug("0x%x: Gap: %d:%02d:%02d, Cts: %d, CPM: %.1f" % (self._offset, gap // 3600, gap % 3600 // 60, gap % 60, cts, cts / gap * 60))
					self._gotcounts(gap, cts)
				elif peek == 0x0c:
					self._log.debug("0x%x: Interval 10 seconds" % (self._offset))
					self._nextbytes(1)
					self._interval = 10
				elif peek == 0x0b:
					self._log.debug("0x%x: Interval 30 Seconds" % (self._offset))
					self._nextbytes(1)
					self._interval = 30
				elif peek == 0x0a:
					self._log.debug("0x%x: Interval 1 minute" % (self._offset))
					self._nextbytes(1)
					self._interval = 60
				elif peek == 0x09:
					self._log.debug("0x%x: Interval 2 minutes" % (self._offset))
					self._nextbytes(1)
					self._interval = 2 * 60
				elif peek == 0x08:
					self._log.debug("0x%x: Interval 5 minutes" % (self._offset))
					self._nextbytes(1)
					self._interval = 5 * 60
				elif peek == 0x07:
					self._log.debug("0x%x: Interval 10 minutes" % (self._offset))
					self._nextbytes(1)
					self._interval = 10 * 60
				elif peek == 0x06:
					self._log.debug("0x%x: Interval 30 minutes" % (self._offset))
					self._nextbytes(1)
					self._interval = 30 * 60
				elif peek == 0x05:
					self._log.debug("0x%x: Interval 1 hour" % (self._offset))
					self._nextbytes(1)
					self._interval = 1 * 3600
				elif peek == 0x04:
					self._log.debug("0x%x: Interval 2 hours" % (self._offset))
					self._nextbytes(1)
					self._interval = 2 * 3600
				elif peek == 0x03:
					self._log.debug("0x%x: Interval 12 hours" % (self._offset))
					self._nextbytes(1)
					self._interval = 12 * 3600
				elif peek == 0x02:
					self._log.debug("0x%x: Interval 1 day" % (self._offset))
					self._nextbytes(1)
					self._interval = 1 * 86400
				elif peek == 0x01:
					self._log.debug("0x%x: Interval 3 days" % (self._offset))
					self._nextbytes(1)
					self._interval = 3 * 86400
				elif peek == 0x00:
					self._log.debug("0x%x: Interval 7 days" % (self._offset))
					self._nextbytes(1)
					self._interval = 7 * 86400
				elif peek == 0xf3:
					self._log.warn("0x%x: Unknown command 0xf3" % (self._offset))
					self._nextbytes(1)
				elif peek == 0xf4:
					self._log.warn("0x%x: Unknown command 0xf4" % (self._offset))
					self._nextbytes(1)
				else:
					self._log.error("0x%x: Unknown special 0x%x encountered" % (self._offset, peek))
					sys.exit(1)
			
			elif peek == 0xfa:
				self._log.warn("0x%x: Next count value is overflowed", self._offset)
				self._nextbytes(1)
				self._overflow = True

			else:
				counts = self._expcts(self._nextbytes(2))
				self._gotcounts(self._interval, counts, self._overflow)
				self._overflow = False


