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

import sys
import datetime
import logging
import hashlib

import Globals
import OutputBackends

from GSProtocolHandler import GSProtocolHandler
from GSProtocolHandlerVers1 import GSProtocolHandlerVers1
from LogDataParserVers1 import LogDataParserVers1
from GSProtocolHandlerVers2 import GSProtocolHandlerVers2
from LogDataParserVers2 import LogDataParserVers2
from RS232Connection import RS232Connection
from SimulatedConnection import SimulatedConnection
from InvalidConnection import InvalidConnection
from GSOnline import GSOnline
from Exceptions import InvalidArgumentException
from HexDump import HexDump

class GammaCommands():
	def __init__(self, args):
		self._log = logging.getLogger("gsu.cmds." + self.__class__.__name__)
		self._args = args
		self._protocolhandler = {
			"v1":		GSProtocolHandlerVers1,
			"v2":		GSProtocolHandlerVers2,
		}[args["protocol"]]
		self._conn = None
		self._device = None
		self._logcache = None

	def connect(self):
		if not self._args["nodevice"]:
			if not self._args["simulate"]:
				self._conn = RS232Connection(self._args)
			else:
				self._conn = SimulatedConnection(self._args)
		else:
			self._conn = InvalidConnection(self._args)
		self._device = self._protocolhandler(self._conn)
		if not self._args["nodevice"]:
			# Switch to a known mode state if possible
			self._device.initmode()

	def execute(self):
		for command in self._args.getcommands():
			methodname = "_cmd_" + command.name
			try:
				method = getattr(self, methodname)
			except AttributeError:
				raise InvalidArgumentException("Programming error: no such method '%s' -- please notify %s!" % (methodname, Globals.AUTHOR_AND_EMAIL))
			method(*command.args)
		self._device.close()

	def _cmd_identify(self):
		version = self._device.getversion()
		if "datetime" in version:
			print("Current date and time: %s" % (version["datetime"].strftime("%Y-%m-%d %H:%M:%S")))
		if "serial" in version:
			print("Serial number        : %d" % (version["serial"]))
		if "version" in version:
			print("Software version     : %s" % (version["version"]))
		if "buffill" in version:
			print("Log buffer fill      : %d bytes" % (version["buffill"]))

	def _cmd_synctime(self):
		self._device.settime(datetime.datetime.now())

	def _cmd_syncutctime(self):
		self._device.settime(datetime.datetime.utcnow())

	def _cmd_settime(self, date):
		try:
			date = datetime.datetime.strptime(date, "%Y-%m-%d-%H-%M-%S")
		except ValueError as msg:
			raise InvalidArgumentException("format string for 'settime' command invalid: '%s'" % (date))
		self._device.settime(date)

	def _getrawlog(self, infilename):
		if self._logcache is not None:
			return self._logcache

		if infilename is None:
			# Read from device
			(logsize, logdata) = self._device.readlog()
		else:
			# Read from binary file
			(logsize, logdata) = OutputBackends.OutputBackendBIN.readdata(infilename, self._args["force"])

		if not self._args["nologcache"]:
			self._logcache = (logsize, logdata)
		return (logsize, logdata)

	def _cmd_readbinlog(self, infilename, outformat, filename):
		accepted_formats = set([ "txt", "sqlite", "csv", "bin", "xml", "sql", "mysql" ])
		if outformat not in accepted_formats:
			raise InvalidArgumentException("'readlog' command expects one of %s as file format, but '%s' given." % (", ".join(sorted(list(accepted_formats))), outformat))
		(logsize, logdata) = self._getrawlog(infilename)

		backendclass = OutputBackends.getbackendbyname(outformat)
		backend = backendclass(filename, self._args)
		backend.initdata(logsize, logdata)
		parserclass = {
			"v1":		LogDataParserVers1,
			"v2":		LogDataParserVers2,
		}[self._args["protocol"]]
		parserclass(logdata, backend).parse(logsize)
		backend.close()

	def _cmd_readlog(self, outformat, filename):
		self._cmd_readbinlog(None, outformat, filename)

	def _cmd_clearlog(self):
		self._device.clearlog()

	def _cmd_readcfg(self, filename):
		blob = self._device.readconfig()
		outfile = open(filename, "wb")
		outfile.write(blob)
		outfile.close()

	def _cmd_devicereset(self):
		if not self._args["force"]:
			raise InvalidArgumentException("Will NOT execute device reset (--force wasn't specified).")
		else:
			self._device.devicereset()

	def _cmd_online(self, interval, outformat, filename):
		interval = int(interval)
		accepted_formats = set([ "txt", "csv", "sql" ])
		if outformat not in accepted_formats:
			raise InvalidArgumentException("'online' command expects one of %s as file format, but '%s' given." % (", ".join(sorted(list(accepted_formats))), outformat))
		if not GSOnline.intervaltime_possible(interval):
			raise InvalidArgumentException("'online' command does not support interval of %d seconds, valid choices are %s." % (interval, GSOnline.possible_interval_str()))

		intervalcode = GSOnline.intervaltime_to_cmd(interval)
		backendclass = OutputBackends.getbackendbyname(outformat)
		backend = backendclass(filename, self._args)

		self._device.setonlineinterval(intervalcode)
		while True:
			reading = self._device.readonlinevalue()
			if reading is None:
				continue

			fromts = reading.utctimestamp - datetime.timedelta(0, reading.interval)
			backend.newinterval(fromts, reading.utctimestamp, reading.counts)

			if reading.interval != interval:
				# Gamma Scout decided to switch intervals on its own, bring it
				# back on track
				self._device.setonlineinterval(intervalcode)

	def _cmd_switchmode(self, mode):
		mode = mode.lower()
		if mode not in GSProtocolHandler.VALID_MODES:
			raise InvalidArgumentException("'switchmode' command expects one of %s as a parameter." % (", ".join(GSProtocolHandler.VALID_MODES)))
		self._device.switchmode(mode)
		self._log.info("Shutting down after mode switch")
		sys.exit(0)

	def _cmd_devidentify(self):
		blob = self._device.readconfig()
		hashvalue = hashlib.md5(blob).hexdigest()
		knowndigests = {
			"d1e4b979535582f2141dc71a874890e7":		"GS Alert",
			"e8b467526eff14da69a64fe111c8cb6f":		"GS Online/Rechargable",
			"e2d8e9ae015ef0851034e23220351efd":		"GS ?",
		}
		print("%d bytes of calibration data" % (len(blob)))
		print("Calibration hash value %s" % (hashvalue))
		HexDump().dump(blob)
		if hashvalue in knowndigests:
			print("Your device has a known calibration value, it registers as a %s" % (knowndigests[hashvalue]))
		else:
			print("Your device has an unknown calibration value, please mail this whole output to %s" % (Globals.AUTHOR_AND_EMAIL))

	def close(self):
		if (self._conn is not None) and (not self._args["nodevice"]):
			self._device.close()


