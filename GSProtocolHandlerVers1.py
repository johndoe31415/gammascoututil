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

import datetime
import logging

from GSProtocolHandler import GSProtocolHandler
from RE import RE
from Exceptions import CommunicationException

class GSProtocolHandlerVers1(GSProtocolHandler):
	_version_pc_regex = RE(" Version ([0-9]\\.[0-9]{2})")

	def __init__(self, connection):
		GSProtocolHandler.__init__(self, connection)
		self._log = logging.getLogger("gsu.proto." + self.__class__.__name__)

	def initmode(self):
		# Not possible in v1
		pass

	def switchmode(self, newmode):
		# Not possible in v1
		raise CommunicationException("feature", "Gamma Scout Basic does not support switching the mode.")

	def settime(self, timestamp):
		assert(isinstance(timestamp, datetime.datetime))
		command = "d%02d%02d%02d" % (timestamp.day, timestamp.month, timestamp.year - 2000)
		self._conn.writeslow(command)
		self._conn.expectresponse(" Datum gestellt ")
		
		command = "u%02d%02d%02d" % (timestamp.hour, timestamp.minute, timestamp.second)
		self._conn.writeslow(command)
		self._conn.expectresponse(" Zeit gestellt ")

	def synctime(self, utctime = False):
		if utctime:
			self.settime(datetime.datetime.utcnow())
		else:
			self.settime(datetime.datetime.now())

	def getversion(self):
		self._conn.write("v")
		versionstr = self._conn.waitforline(2)
		if versionstr is None:
			# Timeout, no response
			raise CommunicationException("timeout", "Timeout waiting for version reply.")
		versionstr = versionstr[1]

		result = { "Mode": GSProtocolHandler.MODE_PC }
		if GSProtocolHandlerVers1._version_pc_regex.match(versionstr):
			result["version"] = GSProtocolHandlerVers1._version_pc_regex[1]
		else:
			if versionstr in [ "Standard", "ONLINE" ]:
				raise CommunicationException("feature", "You are trying to communicate with a v2 Gamma Scout using the v1 protocol. Please select protocol version v2.")
			raise CommunicationException("unparsable", "Unparsable version string '%s'." % (versionstr))
		return result

	def readlog(self):
		self._conn.write("b")
		self._conn.expectresponse(" GAMMA-SCOUT Protokoll ")
	
		log = [ ]
		linecnt = 0
		while True:
			linecnt += 1
			nextmsg = self._conn.waitforline(1, 3.0)
			if nextmsg is None:
				self._log.error("Timeout while waiting for protocol line")
				break
			if linecnt == 1:
				continue
			logdata = [ int(nextmsg[(3 * i) + 6: (3 * i) + 8], 16) for i in range(16) ]
			log += logdata

			if nextmsg.startswith(" 07f0 "):
				# We're finished
				break
		return (len(log), bytes(log))

	def clearlog(self):
		self._conn.write("z")
		self._conn.expectresponse(" Protokollspeicher wieder frei ")
	
	def devicereset(self):
		self._conn.write("i")
	
	def readconfig(self):
		raise CommunicationException("feature", "Gamma Scout Basic does not support reading configuration block.")

	def close(self):
		self._conn.close()

