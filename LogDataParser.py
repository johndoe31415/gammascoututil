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
		if timesecs is None:
			print("Got no timesecs, but %d counts, ignoring." % (counts), file = sys.stderr)
			return
		if self._curdate is None:
			print("Got timesecs %s, counts %d without an initial timevalue, ignoring." % (str(timesecs), counts), file = sys.stderr)
			return
		todate = self._curdate + datetime.timedelta(0, timesecs)
		self._output.newinterval(self._curdate, todate, counts)
		self._debug("%s - %s: %d" % (self._curdate, todate, counts))
		self._curdate = todate

	def _expcts(counts):
		"""Convert counts from Mirow's exponential representation into an
		integer."""
		(exponent, mantissa) = ((counts[0] & 0xfc) >> 2, ((counts[0] & 0x03) << 8) | counts[1])
		exponent = (exponent + 1) // 2
		if exponent == 0:
			counts = mantissa
		else:
			counts = (mantissa + (2 ** 10)) * (2 ** (exponent - 1))
		return counts

