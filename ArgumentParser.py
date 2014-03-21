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
import collections
import textwrap

import Globals
import OutputBackends
from FriendlyArgumentParser import FriendlyArgumentParser
from GSOnline import GSOnline

ArgDefinitionCls = collections.namedtuple("ArgDefinition", [ "name", "args", "help" ])
def ArgDefinition(**kwargs):
	if "args" not in kwargs:
		kwargs["args"] = tuple()
	return ArgDefinitionCls(**kwargs)
ParsedCommand = collections.namedtuple("ParsedCommand", [ "name", "args" ])

class ArgumentParser():
	def __init__(self):
		self._parser = FriendlyArgumentParser(prog = sys.argv[0], description = "Tool to communicate with Gamma Scout geiger counters and read out the radiation log", add_help = False)
		self._parser.add_argument("-d", "--device", metavar = "device", type = str, default = "/dev/ttyUSB0", help = "Specifies the device that the Gamma Scout is connected to. For debugging purposes, 'sim' may be specified to include simulation sources. Default is %(default)s")
		self._parser.add_argument("-p", "--protocol", metavar = "version", type = str, choices = [ "v1", "v2" ], default = "v2", help = "Specifies the device protocol the connected Gamma Scout uses. Older models use v1 while newer versions use v2. Possible options are %(choices)s, default is %(default)s")
		self._parser.add_argument("--simulate", action = "store_true", help = "Do not connect to a real Gamma Scout device, but connect to a simulator (device name should be UNIX socket)")
		self._parser.add_argument("--force", action = "store_true", help = "Allow execution of commands that are not usually needed by the user (you should only use this if you know what you're doing)")
		self._parser.add_argument("-v", "--verbose", action = "count", default = 0, help = "Show mode logging info. May be specified multiple times to increasse verbosity")
		self._parser.add_argument("--help", action = "store_true", help = "Show this help page and exit")
		self._parser.add_argument("--localstrftime", action = "store_true", help = "For replacement format string, use local time instead of UTC. By default, UTC is chosen.")
		self._parser.add_argument("--noheader", action = "store_true", help = "When printing data in a textual representation, omit the headline")
		self._parser.add_argument("--nologcache", action = "store_true", help = "When executing the readlog command multiple times, read out the log every single time (default is to cache subsequent calls to readlog)")
		self._parser.add_argument("--nodevice", action = "store_true", help = "Do not connect to a Gamma Scout device or to a simulator instance, but just perform offline commands (like log conversion)")
		self._parser.add_argument("--line-buffered", action = "store_true", help = "Flush the output buffers of files after every line. Useful if you are connecting GammaScoutUtil to a pipe and want to directly process the values")
		self._parser.add_argument("--timeout-factor", metavar = "factor", type = float, default = 1.0, help = "Multiply all timeout values with a specific coefficient. Can be used if the Gamma Scout frequently times out. Default is %(default).1f")
		self._parser.add_argument("--txt-format", metavar = "fmtstr", type = str, help = "Sets the output string for the txt output backend. Named printf arguments must be used; recognized names are %s" % (", ".join(OutputBackends.OutputBackendTXT.get_known_args())))
		self._parser.add_argument("--gstool-txt-format", action = "store_true", help = "Shortcut for --txt-format which sets the output format string that gstool uses")
		self._parser.add_argument("--date-format", metavar = "fmtstr", type = str, default = "%Y-%m-%d %H:%M:%S", help = "Sets the strftime format string for the txt and csv output backends. Default is %(default)s")
		self._parser.add_argument("commands", metavar = "command", type = str, nargs = "+", help = "Commands that are processed by the Gamma Scout util, in order of occurence")
		self._commands = [
			ArgDefinition(name = "identify", help = "Displays information like the Gamma Scout software version and serial number of the device"),
			ArgDefinition(name = "devidentify", help = "Output extended information about the Gamma Scout for development purposes"),
			ArgDefinition(name = "synctime", help = "Synchronizes the time with the current local system time (not recommended)"),
			ArgDefinition(name = "syncutctime", help = "Synchronizes the time with the current time in UTC (GMT+0), preferred way of syncing the Gamma Scout time"),
			ArgDefinition(name = "settime", args = [ "YYYY-MM-DD-HH-MM-SS" ], help = "Sets the time to the user defined value"),
		 	ArgDefinition(name = "readlog", args = [ "[txt|sqlite|csv|xml|bin|sql]", "[Filename/Connstr]" ], help = "Reads out Gamma Scout log in text format, SQLite3 format, CSV, XML or binary format and writes the results to the specified filename; only binary data can later on be imported back using the 'readbinlog' command"),
		 	ArgDefinition(name = "readbinlog", args = [ "[Infile]", "[txt|sqlite|csv|xml|bin]", "[Outfile]" ], help = "Reads a Gamma Scout log from a previously written binary file"),
			ArgDefinition(name = "clearlog", help = "Deletes the Gamma Scout log"),
			ArgDefinition(name = "readcfg", args = [ "[Filename]" ], help = "Reads out the configuration blob and writes it in the specified file in binary format"),
			ArgDefinition(name = "devicereset", help = "Completely resets the device to its factory defaults. Do not perform this operation unless you have a good reason to. Requires the --force option to be set in order to work"),
			ArgDefinition(name = "online", args = [ "[Intervaltime]", "[txt|csv|sql]", "[Filename/Connstr]" ], help = "Switches the Gamma Scout into online-mode and records the values it receives continuously into the given file in the specified syntax (every n seconds). Valid intervals are " + GSOnline.possible_interval_str() + " seconds"),
			ArgDefinition(name = "switchmode", args = [ "[standard|pc|online]" ], help = "Switches the Gamma Scout into the desired mode and then exits (leaving it in that mode)"),
		]
		self._knowncommands = { cmd.name: cmd for cmd in self._commands }
		
		orig_printhelp = self._parser.print_help
		def printhelp(*args, **kwargs):
			orig_printhelp(*args, **kwargs)
			print(file = sys.stderr)
			print("commands:", file = sys.stderr)
			for cmd in self._commands:
				if len(cmd.args) == 0:
					print("  %s" % (cmd.name), file = sys.stderr)
				else:
					print("  %s:%s" % (cmd.name, ":".join(cmd.args)), file = sys.stderr)
				for line in textwrap.wrap(cmd.help, initial_indent = "    ", subsequent_indent = "    "):
					print(line, file = sys.stderr)
			print(file = sys.stderr)
			print("examples:", file = sys.stderr)
			print("  Identify a Gamma Scout v1 at /dev/ttyS0:", file = sys.stderr)
			print("    %s -p v1 -d /dev/ttyS0 identify" % (sys.argv[0]), file = sys.stderr)
			print("  Identify a Gamma Scout v2 at /dev/ttyUSB3:", file = sys.stderr)
			print("    %s -d /dev/ttyUSB3 identify" % (sys.argv[0]), file = sys.stderr)
			print("  Read out Gamma Scout log into SQLite database, clear log and sync UTC time:", file = sys.stderr)
			print("    %s readlog:sqlite:/home/joe/gslog.sqlite clearlog syncutctime" % (sys.argv[0]), file = sys.stderr)
			print("  Connect to simulator and read out log of simulator:", file = sys.stderr)
			print("    %s -d simsocket --simulate readlog:csv:outfile.csv" % (sys.argv[0]), file = sys.stderr)
			print("  Read in binary blob log and write into database without any device:", file = sys.stderr)
			print("    %s --nodevice readbinlog:v2log.bin:sqlite:database.sqlite" % (sys.argv[0]), file = sys.stderr)
			print("  Read in v1 binary blob log and print it on standard output:", file = sys.stderr)
			print("    %s --nodevice -p v1 readbinlog:v1log.bin:txt:-" % (sys.argv[0]), file = sys.stderr)
			print("  Read Gamma Scout log into file that is named after current date and time:", file = sys.stderr)
			print("    %s readlog:txt:%%Y/%%m/%%Y-%%m-%%d-%%H-%%M-%%S.txt" % (sys.argv[0]), file = sys.stderr)
			print("  Read out log, write it to binary file and to database and clear log of Gamma Scout afterwards:", file = sys.stderr)
			print("    %s readlog:bin:%%Y/%%m/%%Y-%%m-%%d-%%H-%%M-%%S.txt readlog:sqlite:database.sqlite clearlog" % (sys.argv[0]), file = sys.stderr)
			print()
			print("notes:", file = sys.stderr)
			notes = [
				"for the txt, csv and xml output backends, '-' may be speficied as filename which will cause the output to be printed on stdout",
				"filenames support strftime substitutions",
				"if filename specification contain subdirectories, they will be created if they do not exist",
				"the 'sql' output backend does not take a filename, but a connection string in the form key1=value1,key2=value2,... and so on. Recognized keys are dbdialect, dbname, tablename, file",
			]
			for note in notes:
				for line in textwrap.wrap(note, initial_indent = "  - ", subsequent_indent = "    "):
					print(line, file = sys.stderr)
			print()
			print("version: %s" % (Globals.VERSION))
		self._parser.print_help = printhelp

		self._parsedcmds = [ ]

	def parseordie(self):
		self._args = self._parser.parse_args(sys.argv[1:])
		if self._args.help:
			self._parser.print_help(file = sys.stderr)
			sys.exit(0)
		
		for command in self._args.commands:
			command = command.split(":")

			cmdname = command[0]
			cmdargs = command[1:]
			if cmdname not in self._knowncommands:
				self._parser.error("'%s' is not a known command; known commands are %s." % (cmdname, ", ".join(sorted(list(self._knowncommands)))))
			
			cmddef = self._knowncommands[cmdname]
			if len(cmdargs) != len(cmddef.args):
				self._parser.error("Command '%s' takes %d parameter(s), but you supplied %d parameter(s)." % (cmdname, len(cmddef.args), len(cmdargs)))

			cmd = ParsedCommand(cmdname, cmdargs)
			self._parsedcmds.append(cmd)

	def __getitem__(self, key):
		return getattr(self._args, key)

	def getcommands(self):
		return iter(self._parsedcmds)

