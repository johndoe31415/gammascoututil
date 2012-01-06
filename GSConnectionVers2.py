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
from CommunicationError import CommunicationError
from RE import RE

class GSConnectionVers2(GSConnection):
	_version_pc_regex = RE("Version ([0-9]\.[0-9]{2}) " + RE.GDECIMAL + " " + RE.GHEXADECIMAL + " ([0-9]{2})\.([0-9]{2})\.([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})")
	_config_firstline_regex = RE(RE.GHEXADECIMAL + " " + RE.GHEXADECIMAL + " " + RE.GHEXADECIMAL)

	def __init__(self, device, debugmode = False):
		GSConnection.__init__(self, device, 9600, debugmode)

	def settime(self, timestamp):
		assert(isinstance(timestamp, datetime.datetime))
		self._switchmode("PC")
		command = "t%02d%02d%02d%02d%02d%02d" % (timestamp.day, timestamp.month, timestamp.year - 2000, timestamp.hour, timestamp.minute, timestamp.second)
		self._writeslow(command)
		self._expectresponse("Datum und Zeit gestellt")

	def synctime(self, utctime = False):
		if utctime:
			self.settime(datetime.datetime.utcnow())
		else:
			self.settime(datetime.datetime.now())

	def getversion(self, reqmode = None):
		if reqmode is not None:
			self._switchmode(reqmode)
		self._write("v")
		if self._nextmsg() is None:
			# Timeout, no response
			raise CommunicationError("timeout", "Timeout waiting for first datagram of version.")
		
		versionstr = self._nextmsg()
		if versionstr is None:
			# Timeout, no response
			raise CommunicationError("timeout", "Timeout waiting for second datagram of version.")

		result = { "Mode": None }
		if versionstr == "Standard":
			result["Mode"] = "Standard"
		elif GSConnectionVers2._version_pc_regex.match(versionstr):
			result["Mode"] = "PC"
			result["version"] = GSConnectionVers2._version_pc_regex[1]
			result["serial"] = int(GSConnectionVers2._version_pc_regex[2])
			result["buffill"] = int(GSConnectionVers2._version_pc_regex[3], 16)
			day = int(GSConnectionVers2._version_pc_regex[4])
			mon = int(GSConnectionVers2._version_pc_regex[5])
			year = int(GSConnectionVers2._version_pc_regex[6]) + 2000
			hour = int(GSConnectionVers2._version_pc_regex[7])
			mint = int(GSConnectionVers2._version_pc_regex[8])
			sec = int(GSConnectionVers2._version_pc_regex[9])
			result["datetime"] = datetime.datetime(year, mon, day, hour, mint, sec)
		else:
			raise CommunicationError("unparsable", "Unparsable version string '%s'." % (versionstr))
		return result

	def _switchmode(self, newmode):
		assert(newmode in [ "Standard", "PC" ])
		currentmode = self.getversion()["Mode"]
		if currentmode == newmode:
			# Already done!
			return

		if newmode == "Standard":
			# Switch to standard mode, end PC mode
			self._write("X")
			self._expectresponse("PC-Mode beendet", 2)
		elif newmode == "PC":
			# Switch to PC mode
			self._write("P")
			self._expectresponse("PC-Mode gestartet", 2)

	def _linechecksum(data):
		return sum(data[0 : -1]) & 0xff

	def readlog(self):
		self._switchmode("PC")
		buffill = self.getversion()["buffill"]
		self._write("b")
		self._expectresponse("GAMMA-SCOUT Protokoll")
	
		log = [ ]
		linecnt = 0
		while True:
			linecnt += 1
			nextmsg = self._nextmsg()
			if nextmsg is None:
				break
			if (len(nextmsg) % 2) != 0:
				raise CommunicationError("unparsable", "Protocol line was not a multiple of two bytes (%d bytes received)." % (len(nextmsg)))

			logdata = [ int(nextmsg[2 * i : 2 * i + 2], 16) for i in range(len(nextmsg) // 2) ]
			calcchksum = GSConnectionVers2._linechecksum(logdata)
			if calcchksum != logdata[-1]:
				# Warn about this only, cannot do anything anyways
				print("Warning: Log line %d has checksum error, calculated 0x%x, transmitted 0x%x." % (calcchksum, logdata[-1]), file = sys.stderr)

			log += logdata[:-1]

		return (buffill, bytes(log))

	def clearlog(self):
		self._switchmode("PC")
		self._write("z")
		self._expectresponse("Protokollspeicher wieder frei")
	
	def devicereset(self):
		self._switchmode("PC")
		self._write("i")
	
	def readconfig(self):
		self._switchmode("PC")
		self._write("c")
		linecnt = 0
		result = { }
		log = [ ]
		while True:
			linecnt += 1
			nextmsg = self._nextmsg()
			if nextmsg is None:
				break
			if linecnt == 2:
				if not GSConnectionVers2._config_firstline_regex.match(nextmsg):
					raise CommunicationError("unparsable", "First configuration data line format unexpected (received '%s')." % (nextmsg))
				log.append(int(GSConnectionVers2._config_firstline_regex[1], 16))
				log.append(int(GSConnectionVers2._config_firstline_regex[2], 16))
				nextmsg = GSConnectionVers2._config_firstline_regex[3]

			if linecnt >= 2:
				logdata = [ int(nextmsg[2 * i : 2 * i + 2], 16) for i in range(len(nextmsg) // 2) ]
				log += logdata
		return bytes(log)

	def close(self):
		try:
			self._switchmode("Standard")
		except CommunicationError as e:
			print("Unabled to switch back to standard mode: %s" % (str(e)), file = sys.stderr)
		GSConnection.close(self)

