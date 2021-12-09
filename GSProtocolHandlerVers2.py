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

import re
import sys
import datetime
import collections
import logging
import time

from GSProtocolHandler import GSProtocolHandler
from Exceptions import CommunicationException
from RE import RE

OnlineResults = collections.namedtuple("OnlineResults", [ "utctimestamp", "interval", "counts" ])

class GSProtocolHandlerVers2(GSProtocolHandler):
	_version_pc_regex = RE("Version ([0-9]\.[0-9]{2}) " + RE.GDECIMAL + " " + RE.GHEXADECIMAL + " ([0-9]{2})\.([0-9]{2})\.([0-9]{2}) ([0-9]{2}):([0-9]{2}):([0-9]{2})")
	_version_v1_regex = re.compile("^ Version (?P<version>[0-9]\.[0-9]{2})$")
	_config_firstline_regex = RE(RE.GHEXADECIMAL + " " + RE.GHEXADECIMAL + " " + RE.GHEXADECIMAL)
	_online_regex = re.compile("^I(?P<interval>[0-9a-f]{4})(?P<counts>[0-9a-f]{6})$")

	def __init__(self, connection):
		GSProtocolHandler.__init__(self, connection)
		self._log = logging.getLogger("gsu.proto." + self.__class__.__name__)
		self._currentmode = None

	def initmode(self):
		# We have no idea in which state the Gamma Scout is at the moment, so
		# we need to find out which one it is. We can always switch to Standard
		# mode, but this will cause no reaction if it is already in standard
		# mode (and therefore cause a delay because of the subsequent timeout).
		# Since assuming it is in default mode is a good assumption, we'll try
		# to get a version reply first and only switch to standard mode if that
		# fails
		self._currentmode = None
		self._conn.write("v")
		versionstr = self._conn.waitforline(2)
		if (versionstr is None) or (versionstr[1] != "Standard"):
			# This didn't work. Is it maybe a v1 device that we try to speak to
			# using a v2 protocol?
			if versionstr is not None:
				match = GSProtocolHandlerVers2._version_v1_regex.match(versionstr[1])
				if match is not None:
					# Set connection to None to avoid trying to close it
					self._conn.close()
					self._conn = None
					raise CommunicationException("feature", "You are trying to communicate with a v1 Gamma Scout (version %s) using the v2 protocol. Please select protocol version v1." % (match.groupdict()["version"]))
			self._log.info("Initial GS mode determination failed, returned %s." % (str(versionstr)))
			self.switchmode(GSProtocolHandler.MODE_STANDARD)
		else:
			self._log.debug("Initial GS mode determination succeeded, GS in standard mode.")
			self._currentmode = GSProtocolHandler.MODE_STANDARD

	def settime(self, timestamp):
		assert(isinstance(timestamp, datetime.datetime))
		self.switchmode(GSProtocolHandler.MODE_PC)
		command = "t%02d%02d%02d%02d%02d%02d" % (timestamp.day, timestamp.month, timestamp.year % 100, timestamp.hour, timestamp.minute, timestamp.second)
		self._conn.writeslow(command)
		self._conn.expectresponse("Datum und Zeit gestellt")

	def setonlineinterval(self, interval):
		assert(isinstance(interval, int))
		assert(0 <= interval <= 9)
		self.switchmode(GSProtocolHandler.MODE_ONLINE)
		self._conn.write(str(interval))

	def readonlinevalue(self):
		line = self._conn.waitforline(1)
		if line is not None:
			result = GSProtocolHandlerVers2._online_regex.match(line)
			if result:
				result = { key: int(value, 16) for (key, value) in result.groupdict().items() }
				return OnlineResults(utctimestamp = datetime.datetime.utcnow(), interval = result["interval"], counts = result["counts"])

	def getversion(self):
		self.switchmode(GSProtocolHandler.MODE_PC)
		self._conn.write("v")

		versionstr = self._conn.waitforline(2)
		if versionstr is None:
			# Timeout, no response
			raise CommunicationException("timeout", "Timeout waiting for version reply.")
		versionstr = versionstr[1]

		result = { "Mode": None }
		if versionstr == "Standard":
			result["Mode"] = GSProtocolHandler.MODE_STANDARD
		elif GSProtocolHandlerVers2._version_pc_regex.match(versionstr):
			result["Mode"] = GSProtocolHandler.MODE_PC
			result["version"] = GSProtocolHandlerVers2._version_pc_regex[1]
			result["serial"] = int(GSProtocolHandlerVers2._version_pc_regex[2])
			result["buffill"] = int(GSProtocolHandlerVers2._version_pc_regex[3], 16)
			day = int(GSProtocolHandlerVers2._version_pc_regex[4])
			mon = int(GSProtocolHandlerVers2._version_pc_regex[5])
			year = int(GSProtocolHandlerVers2._version_pc_regex[6]) + 2000
			hour = int(GSProtocolHandlerVers2._version_pc_regex[7])
			mint = int(GSProtocolHandlerVers2._version_pc_regex[8])
			sec = int(GSProtocolHandlerVers2._version_pc_regex[9])
			result["datetime"] = datetime.datetime(year, mon, day, hour, mint, sec)
		else:
			raise CommunicationException("unparsable", "Unparsable version string '%s'." % (versionstr))
		return result

	def switchmode(self, newmode):
		assert(newmode in GSProtocolHandler.VALID_MODES)
		if self._currentmode == newmode:
			# Already done!
			self._log.debug("Skipping mode switch %s to %s" % (str(self._currentmode), newmode))
			return
		self._log.info("Switching mode from %s to %s" % (str(self._currentmode), newmode))

		if newmode == GSProtocolHandler.MODE_STANDARD:
			# Switch to standard mode, end PC or online mode
			self._conn.write("X")

			# We need a loop here because the GS may be in online mode and may
			# respond with another interval before acknowledging our request to
			# leave the mode
			while True:
				datagram = self._conn.waitforline(1, 3.0)
				if datagram is None:
					raise CommunicationException("timeout", "No appropriate response within defined time when trying to switch to standard mode.")

				if datagram in [ "PC-Mode beendet", "Online-Mode beendet" ]:
					# Standard mode now active
					if datagram == "Online-Mode beendet":
						# The Gamma Scout online frequently chokes when leaving
						# the online mode. It sends at least one \x00 after the
						# last \r\n which means the interpretation of the next
						# message would be garbled if we do not clear the
						# buffer here. Additionally, it takes a rather long
						# time before being responsive to the next command
						# again. We solve both by waiting a bit (until it is
						# responsive again) and clearing the buffer afterwards
						# (to get rid of any excess \x00)
						time.sleep(0.5)
						self._conn.clearrxbuf()
					break
		elif newmode == GSProtocolHandler.MODE_PC:
			if self._currentmode == GSProtocolHandler.MODE_ONLINE:
				# Switch to standard mode first
				self.switchmode(GSProtocolHandler.MODE_STANDARD)

			# Switch to PC mode
			self._conn.write("P")
			self._conn.expectresponse("PC-Mode gestartet", 3)
		elif newmode == GSProtocolHandler.MODE_ONLINE:
			if self._currentmode == GSProtocolHandler.MODE_PC:
				# Switch to standard mode first
				self.switchmode(GSProtocolHandler.MODE_STANDARD)

			# Switch to PC mode
			self._conn.write("O")
			datagram = self._conn.waitforline(1)
			if (datagram is None) or (not datagram.startswith("S")):
				raise CommunicationException("unparsable", "Unparsable response when trying to enter online mode; expected \"S...\" but got '%s'" % (str(datagram)))

		self._currentmode = newmode

	@staticmethod
	def _linechecksum(data):
		return sum(data[0 : -1]) & 0xff

	def readlog(self):
		self.switchmode(GSProtocolHandler.MODE_PC)
		buffill = self.getversion()["buffill"]
		self._conn.write("b")
		self._conn.expectresponse("GAMMA-SCOUT Protokoll")

		log = [ ]
		linecnt = 0
		while True:
			linecnt += 1
			nextmsg = self._conn.waitforline()
			if nextmsg is None:
				break
			if (len(nextmsg) % 2) != 0:
				raise CommunicationException("unparsable", "Protocol line was not a multiple of two bytes (%d bytes received)." % (len(nextmsg)))

			logdata = [ int(nextmsg[2 * i : 2 * i + 2], 16) for i in range(len(nextmsg) // 2) ]
			calcchksum = GSProtocolHandlerVers2._linechecksum(logdata)
			if calcchksum != logdata[-1]:
				# Warn about this only, cannot do anything anyways
				print("Warning: Log line %d has checksum error, calculated 0x%x, transmitted 0x%x." % (linecnt, calcchksum, logdata[-1]), file = sys.stderr)

			log += logdata[:-1]
		return (buffill, bytes(log))

	def clearlog(self):
		self.switchmode(GSProtocolHandler.MODE_PC)
		self._conn.write("z")
		self._conn.expectresponse("Protokollspeicher wieder frei")

	def devicereset(self):
		self.switchmode(GSProtocolHandler.MODE_PC)
		self._conn.write("i")

	def readconfig(self):
		self.switchmode(GSProtocolHandler.MODE_PC)
		self._conn.write("c")
		linecnt = 0
		result = { }
		log = [ ]
		while True:
			linecnt += 1
			nextmsg = self._conn.waitforline()
			if nextmsg is None:
				break
			if linecnt == 2:
				if not GSProtocolHandlerVers2._config_firstline_regex.match(nextmsg):
					raise CommunicationException("unparsable", "First configuration data line format unexpected (received '%s')." % (nextmsg))
				log.append(int(GSProtocolHandlerVers2._config_firstline_regex[1], 16))
				log.append(int(GSProtocolHandlerVers2._config_firstline_regex[2], 16))
				nextmsg = GSProtocolHandlerVers2._config_firstline_regex[3]

			if linecnt >= 2:
				logdata = [ int(nextmsg[2 * i : 2 * i + 2], 16) for i in range(len(nextmsg) // 2) ]
				log += logdata
		return bytes(log)

	def close(self):
		if self._conn is not None:
			try:
				self.switchmode(GSProtocolHandler.MODE_STANDARD)
			except CommunicationException as e:
				self._log.error("Unable to switch back to standard mode: %s" % (str(e)))
			self._conn.close()
