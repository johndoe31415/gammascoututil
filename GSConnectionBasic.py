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
from GSConnection import GSConnection
from GSBasicSimData import GSBasicSimData
from RE import RE
from CommunicationError import CommunicationError

class GSConnectionBasic(GSConnection):
	_version_pc_regex = RE(" Version ([0-9]\.[0-9]{2})")
	_config_firstline_regex = RE(RE.GHEXADECIMAL + " " + RE.GHEXADECIMAL + " " + RE.GHEXADECIMAL)

	def __init__(self, device, debugmode = False):
		GSConnection.__init__(self, device, 2400, debugmode)
		self._simulation = False
		if self._simulation:
			print("You're running in simulation mode, do not release this version!", file = sys.stderr)

	def _simdata(self, command):
		if self._simulation:
			self._bufferhasitems.acquire()
			self._databuffer += GSBasicSimData()[command]
			self._bufferhasitems.notify_all()
			self._bufferhasitems.release()

	def settime(self, timestamp):
		assert(isinstance(timestamp, datetime.datetime))
		command = "d%02d%02d%02d" % (timestamp.day, timestamp.month, timestamp.year - 2000)
		self._writeslow(command)
		self._simdata("d")
		self._expectresponse(" Datum gestellt ")
		
		command = "u%02d%02d%02d" % (timestamp.hour, timestamp.minute, timestamp.second)
		self._writeslow(command)
		self._simdata("u")
		self._expectresponse(" Zeit gestellt ")

	def synctime(self):
		self.settime(datetime.datetime.now())

	def getversion(self, reqmode = None):
		self._write("v")
		self._simdata("v")
		if self._nextmsg() is None:
			# Timeout, no response
			raise CommunicationError("timeout", "Timeout waiting for first datagram of version.")
		
		versionstr = self._nextmsg()
		if versionstr is None:
			# Timeout, no response
			raise CommunicationError("timeout", "Timeout waiting for second datagram of version.")

		result = { "Mode": "PC" }
		if GSConnectionBasic._version_pc_regex.match(versionstr):
			result["version"] = GSConnectionBasic._version_pc_regex[1]
		else:
			raise CommunicationError("unparsable", "Unparsable version string '%s'." % (versionstr))
		return result

	def readlog(self):
		self._write("b")
		self._simdata("b")
		self._expectresponse(" GAMMA-SCOUT Protokoll ")
	
		log = [ ]
		linecnt = 0
		while True:
			linecnt += 1
			nextmsg = self._nextmsg(3.0)
			if nextmsg is None:
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
		self._write("z")
		self._simdata("z")
		self._expectresponse(" Protokollspeicher wieder frei ")
	
	def devicereset(self):
		self._write("i")
	
	def readconfig(self):
		raise CommunicationError("feature", "Gamma Scout Basic does not support reading configuration block.")

