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

import logging
import sys
import datetime

class LogDataParser():
	def __init__(self, data, outputbackend):
		self._log = logging.getLogger("gsu.parser." + self.__class__.__name__)
		self._data = data
		self._output = outputbackend
		self._curdate = None
		self._interval = None
		self._offset = 0
		self._overflow = False

	@staticmethod
	def _hexdecify(data):
		return [ (10 * ((x & 0xf0) >> 4) + (x & 0x0f))  for x in data ]

	def _peekbyte(self):
		return self._data[self._offset]
	
	def _nextbytes(self, length):
		o = self._offset
		self._offset += length
		return self._data[o : o + length]
	
	def _gotcounts(self, timesecs, counts, overflow = False):
		if timesecs is None:
			self._log.warn("0x%x: Got no timesecs, but %d counts, ignoring (overflow = %s)." % (self._offset, counts, overflow))
			return
		if self._curdate is None:
			self._log.warn("0x%x: Got timesecs %s, counts %d without an initial timevalue, ignoring (overflow = %s)." % (self._offset, str(timesecs), counts, overflow))
			return
		todate = self._curdate + datetime.timedelta(0, timesecs)
		self._output.newinterval(self._curdate, todate, counts)
		self._log.debug("0x%x: %s - %s: %d (overflow = %s)" % (self._offset, self._curdate, todate, counts, overflow))
		self._curdate = todate

	def _expcts(self, expcounts):
		"""Convert counts from Mirow's exponential representation into an
		integer."""
		(exponent, mantissa) = ((expcounts[0] & 0xfc) >> 2, ((expcounts[0] & 0x03) << 8) | expcounts[1])
		exponent = (exponent + 1) // 2
		if exponent == 0:
			counts = mantissa
		else:
			counts = (mantissa + (2 ** 10)) * (2 ** (exponent - 1))
		self._log.debug("0x%x: Exponential count conversion: %s [exp = %d, man = %d] -> %d" % (self._offset, "".join([ "%02x" % (c) for c in expcounts ]), exponent, mantissa, counts))
		return counts


