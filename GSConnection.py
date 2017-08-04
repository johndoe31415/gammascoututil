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

import time

from Exceptions import CommunicationException
from RXBuffer import RXBuffer

class GSConnection():
	def __init__(self, args):
		self._args = args
		self._rxbuf = RXBuffer()

	def expectresponse(self, string, timeout = 1.0):
		assert(isinstance(string, str))

		datagram = self._rxbuf.waitforline(2, timeout * self._args["timeout_factor"])
		if datagram is None:
			raise CommunicationException("timeout", "Waiting for response datagram '%s' timed out after %.1f secs." % (string, timeout))

		if datagram[0] != "":
			raise CommunicationException("unparsable", "Waiting for first response datagram returned '%s' while expecting empty string." % (str(datagram)))
		if datagram[1] != string:
			raise CommunicationException("unparsable", "Waiting for second response datagram returned '%s' while expecting '%s'." % (str(datagram), string))

	def writeslow(self, string):
		"""This will send a string char-by-char with about 1.8 chars/second.
		Pathetically, some commands (such as the set time command) really need
		this or they'll choke and miss characters. All hail to the grand design
		of the Gamma Scout geniusses!"""
		for char in string:
			self.write(char)
			time.sleep(0.55)			# 0.4 is actually too fast, 0.5 works (0.55 is some safety margin)

	def write(self, string):
		"""This will send a string to the Gamma Scout. Note that we do NOT send
		CR/LF at the end of each line when issuing commands or the Gamma Scout
		might choke."""
		raise Exception("Not implemented")

	def waitforline(self, linecnt = 1, timeout = 1.0):
		return self._rxbuf.waitforline(linecnt, timeout * self._args["timeout_factor"])

	def clearrxbuf(self):
		self._rxbuf.clear()

	def close(self):
		pass

