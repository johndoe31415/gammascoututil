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
import getopt
import datetime
import textwrap

from RE import RE
from Decorators import typecheck

class CmdLineParseException(Exception):
	def __init__(self, errorstr):
		Exception.__init__(self, errorstr)


class IntParser():
	@typecheck
	def __init__(self, minval: (int, None), maxval: (int, None)):
		self._minval = minval
		self._maxval = maxval

	@typecheck
	def parse(self, value: str, option):
		parsedvalue = None
		try:
			parsedvalue = int(value)
		except ValueError:
			try:
				parsedvalue = int(value, 16)
			except ValueError:
				pass

		if not parsedvalue:
			raise CmdLineParseException("Supplied value '%s' for option %s cannot be parsed as integer." % (value, str(option)))
		
		if (self._minval is not None) and (parsedvalue < self._minval):
			raise CmdLineParseException("Supplied value %d for option %s is less than the minimum value %d." % (parsedvalue, str(option), self._minval))
		
		if (self._maxval is not None) and (parsedvalue > self._maxval):
			raise CmdLineParseException("Supplied value %d for option %s is more than the maximum value %d." % (parsedvalue, str(option), self._maxval))
	
		return parsedvalue


class DateTimeParser():
	@typecheck
	def parse(self, value: str, option):
		acceptedformats = [
			"%Y-%m-%d %H:%M:%S",
			"%Y-%m-%d",
		]

		if value == "now":
			parsedvalue = datetime.datetime.now()
		else:
			parsedvalue = None
			for acceptedformat in acceptedformats:
				try:
					parsedvalue = datetime.datetime.strptime(value, acceptedformat)
					break
				except ValueError:
					pass
		
		if not parsedvalue:
			raise CmdLineParseException("Supplied value '%s' for option %s cannot be parsed as datetime." % (value, str(option)))

		return parsedvalue

class ExtendedDateTimeParser(DateTimeParser):
	@typecheck
	def _timedeltaconvert(origtime: datetime.datetime, plusminus: str, amount: str, unit: str):
		amount = int(amount)
		assert(unit in [ "m", "h", "d", "w", "M", "Y" ])		# Minute, Hour, Day, Week, Month, Year

		# Convert to -1 or +1
		plusminus = {
			"-":	-1,
			"+":	1,
		}[plusminus]

		resulttime = None
		if unit in "mhdw":
			# These are the easy ones
			multiplier = {
				"m":	60,
				"h":	3600,
				"d":	86400,
				"w":	7 * 86400,
			}
			delta = datetime.timedelta(0, multiplier[unit] * amount)
		elif unit in "MY":
			if unit == "Y":
				amount *= 12
			
			fullyears = amount // 12
			months = amount % 12

			resultyear = origtime.year + (plusminus * fullyears)
			resultmonth = origtime.month + (plusminus * months)
			if resultmonth < 1:
				resultmonth += 12
				resultyear -= 1
			elif resultmonth > 12:
				resultmonth -= 12
				resultyear += 1
			resulttime = datetime.datetime(resultyear, resultmonth, origtime.day, origtime.hour, origtime.minute, origtime.second)

		if resulttime is None:
			if plusminus < 0:
				resulttime = origtime - delta
			else:
				resulttime = origtime + delta
		return resulttime

	@typecheck
	def parse(self, value: str, option):
		datefmt = "[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}"
		accepted_special_format = RE("(now|" + datefmt + ")(?:([+-])([0-9]+)([mhdwMY]))$")
		
		# First check if it's a special case
		if accepted_special_format.match(value):
			# Parse base point first
			startdate = DateTimeParser.parse(self, accepted_special_format[1], option)

			# Then do the arithmetic
			resultdate = ExtendedDateTimeParser._timedeltaconvert(startdate, accepted_special_format[2], accepted_special_format[3], accepted_special_format[4])
			return resultdate
		else:
			# Otherwise pass over to DateTimeParser parent
			return DateTimeParser.parse(self, value, option)


class TimeIntervalParser():
	@typecheck
	def parse(self, value: str, option):
		accepted_format = RE("([0-9]+)([smhdw])$")		# Secs, Mins, Hours, Days, Weeks		
		if accepted_format.match(value):
			multiplier = {
				"s":	1,
				"m":	60,
				"h":	3600,
				"d":	86400,
				"w":	7 * 86400,
			}
			return int(accepted_format[1]) * multiplier[accepted_format[2]]
		else:
			raise CmdLineParseException("Supplied value '%s' for option %s cannot be parsed as time interval." % (value, str(option)))


class EnumParser():
	@typecheck
	def __init__(self, enumvals: set):
		self._enumvals = enumvals

	@typecheck
	def parse(self, value: str, option):
		if value not in self._enumvals:
			raise CmdLineParseException("Supplied value '%s' for option %s is none of the allowed [ %s ]." % (value, str(option), ", ".join(sorted(list(self._enumvals)))))
		return value


class CmdLineOption():
	@typecheck
	def __init__(self, name: str, shortopt: (str, None), longopt: (str, None) = None):
		assert((shortopt is not None) or (longopt is not None))
		assert((shortopt is None) or (len(shortopt) == 1))
		assert(len(name) > 0)
		self._name = name
		self._shortopt = shortopt
		self._longopt = longopt
		self._description = None
		self._minoccurences = 0
		self._maxoccurences = None
		self._parser = None
		self._takesparameters = False
		self._parametername = None
		self._occurences = 0
		self._defaultvalue = None

	def resetoccurences(self):
		self._occurences = 0

	def haveoccurence(self):
		self._occurences += 1

	def checkoccurences(self):
		if (self._minoccurences is not None) and (self._occurences < self._minoccurences):
			raise CmdLineParseException("Option %s should occur at least %d times, but did only occur %d times." % (str(self), self._minoccurences, self._occurences))
		if (self._maxoccurences is not None) and (self._occurences > self._maxoccurences):
			raise CmdLineParseException("Option %s may occur at most %d times, but did occur %d times." % (str(self), self._maxoccurences, self._occurences))
		
	@typecheck
	def setdescription(self, description: str):
		self._description = description
		return self

	@typecheck
	def setdefaultvalue(self, value: str):
		self._defaultvalue = value
		return self

	@typecheck
	def setminmaxoccurence(self, minoccurences: int, maxoccurences: (int, None)):
		assert(minoccurences >= 0)
		assert((maxoccurences is None) or (maxoccurences >= minoccurences))
		self._minoccurences = minoccurences
		self._maxoccurences = maxoccurences
		return self
	
	@typecheck
	def setoccurence(self, occurences: int):
		return self.setminmaxoccurence(occurences, occurences)
	
	@typecheck
	def settakesparameters(self, takesparameters: bool, parametername: (str, None)):
		assert(takesparameters == (parametername is not None))
		self._takesparameters = takesparameters
		self._parametername = parametername
		return self

	def setparser(self, parser):
		self._parser = parser
		return self

	def getshortopt(self) -> (None, str):
		return self._shortopt
	
	def getlongopt(self) -> (None, str):
		return self._longopt

	@typecheck
	def getminoccurences(self) -> int:
		return self._minoccurences
	
	@typecheck
	def getmaxoccurences(self) -> (int, None):
		return self._maxoccurences

	@typecheck
	def gettakesparameters(self) -> bool:
		return self._takesparameters

	def getparser(self):
		return self._parser

	@typecheck
	def getname(self) -> str:
		return self._name

	@typecheck
	def getdescription(self) -> str:
		return self._description
	
	@typecheck
	def getdefaultvalue(self) -> (str, None):
		return self._defaultvalue

	def getshortusagestr(self):
		parm = None
		if self._shortopt is not None:
			if self._takesparameters:
				parm = "-" + self._shortopt + " " + self._parametername
			else:
				parm = "-" + self._shortopt
		return parm

	def getlongusagestr(self):
		parm = None
		if self._longopt is not None:
			if self._takesparameters:
				parm = "--" + self._longopt + "=" + self._parametername
			else:
				parm = "--" + self._longopt
		return parm

	def getusagestr(self):
		parm = self.getlongusagestr() or self.getshortusagestr()

		if self._minoccurences == 0:
			parm = "(" + parm + ")"
		return parm

	def __str__(self):
		return self.getname()

class CmdLineParser():
	def __init__(self):
		self._options = [ ]
		self._parseerr = None
		self._resultdict = { }
		self._resultargs = [ ]
		self._optiondict = { }
		self._optionsanitychecks = {
			"names":		set(),
			"shortopts":	set(),
			"longopts":		set(),
		}

	@typecheck
	def addoption(self, option: CmdLineOption):
		# Make sure names of options are unique
		assert(option.getname() not in self._optionsanitychecks["names"])
		self._optionsanitychecks["names"].add(option.getname())
		
		# Make sure short options are unique
		if option.getshortopt() is not None:
			assert(option.getshortopt() not in self._optionsanitychecks["shortopts"])
			self._optionsanitychecks["shortopts"].add(option.getshortopt())
		
		# Make sure long options are unique
		if option.getlongopt() is not None:
			assert(option.getlongopt() not in self._optionsanitychecks["longopts"])
			self._optionsanitychecks["longopts"].add(option.getlongopt())
		
		self._options.append(option)
		return self
	
	def _equallistsize(list1, list2):
		if len(list1) < len(list2):
			list1 += [ "" ] * (len(list2) - len(list1))
		elif len(list2) < len(list1):
			list2 += [ "" ] * (len(list1) - len(list2))

	def showsyntax(self):
		#nbsp = bytes([ 0xC2, 0xA0 ]).decode("utf-8")
		nbsp = "~"		# Ugly hack, but won't break
		firstline = sys.argv[0] + " "
		for option in self._options:
			firstline += option.getusagestr().replace(" ", nbsp) + " "
	
		# Then wrap
		for line in textwrap.wrap(firstline, 80, subsequent_indent = "    "):
			print(line.replace(nbsp, " "), file = sys.stderr)
		print(file = sys.stderr)

		leftcol = [ ]
		rightcol = [ ]
		for option in self._options:
			addtoleft = ""
			if option.getshortusagestr() is not None:
				addtoleft += option.getshortusagestr().replace(" ", nbsp) + " "
			if option.getlongusagestr() is not None:
				addtoleft += option.getlongusagestr().replace(" ", nbsp) + " "

			addtoright = option.getdescription()
			if option.getdefaultvalue() is not None:
				addtoright += " Defaults to \"%s\"." % (option.getdefaultvalue())

			leftcol += textwrap.wrap(addtoleft, 25)
			rightcol += textwrap.wrap(addtoright, 50)
			CmdLineParser._equallistsize(leftcol, rightcol)

		assert(len(leftcol) == len(rightcol))
		for lineno in range(len(leftcol)):
			print("  %-25s %s" % (leftcol[lineno].replace(nbsp, " "), rightcol[lineno]), file = sys.stderr)

	def _getparseopts(self):
		self._optiondict = { }
		shortparse = ""
		longparse = [ ]
		for option in self._options:
			takesparams = option.gettakesparameters()
			if option.getshortopt():
				shortparse += option.getshortopt()
				if takesparams:
					shortparse += ":"
				self._optiondict["-" + option.getshortopt()] = option

			if option.getlongopt():
				if not takesparams:
					longparse.append(option.getlongopt())
				else:
					longparse.append(option.getlongopt() + "=")
				
				self._optiondict["--" + option.getlongopt()] = option
		return (shortparse, longparse)

	def _clearresults(self):
		self._resultdict = { }

	def _rawparse(self):
		self._clearresults()
		(shortparse, longparse) = self._getparseopts()

		# Use getopt to parse
		(optlist, args) = getopt.getopt(sys.argv[1:], shortparse, longparse)
		self._resultargs = args

		# Reset occurences for each option
		for option in self._options:
			option.resetoccurences()

		# Initialize all occurence counting options to zero
		for option in self._options:
			if not option.gettakesparameters():
				self._resultdict[option.getname()] = 0

		# Then parse the actual options with checkers
		for (optionstr, value) in optlist:
			option = self._optiondict[optionstr]
			option.haveoccurence()
			parser = option.getparser()
			if parser is not None:
				value = parser.parse(value, option)

			if option.gettakesparameters():
				# Value is important
				if option.getmaxoccurences() == 1:
					# Store in dictionary
					self._resultdict[option.getname()] = value
				else:
					# Store in list
					if self._resultdict.get(option.getname()) is None:
						self._resultdict[option.getname()] = [ ]
					self._resultdict[option.getname()].append(value)
			else:
				# No value, just count occurences
				self._resultdict[option.getname()] += 1

		# Finally, initialize unset option to defaults
		for option in self._options:
			if (self._resultdict.get(option.getname()) is None) and (option.getdefaultvalue() is not None):
				value = option.getdefaultvalue()

				parser = option.getparser()
				if parser is not None:
					value = parser.parse(value, option)

				self._resultdict[option.getname()] = value
				if option.getmaxoccurences() > 1:
					self._resultdict[option.getname()] = [ self._resultdict[option.getname()] ]

		# Check if number of occurences is correct
		for option in self._options:
			option.checkoccurences()

#		print("ResDict", self._resultdict)
#		print("ResArgs", self._resultargs)

	def getparseerror(self):
		return self._parseerr

	@typecheck
	def parse(self) -> bool:
		success = False
		try:
			self._rawparse()
			success = True
		except getopt.GetoptError as e:
			self._parseerr = str(e)
		except CmdLineParseException as e:
			self._parseerr = str(e)
		return success

	def parseordie(self):
		if not self.parse():
			print(self.getparseerror(), file = sys.stderr)
			print(file = sys.stderr)
			self.showsyntax()
			sys.exit(1)

	def getargs(self):
		return dict(self._resultargs)

	def __getitem__(self, key):
		return self._resultdict.get(key)

if __name__ == "__main__":
	c = CmdLineParser()

	o = CmdLineOption("integer", "i", "integer").setdescription("This is an integral option with a quite long descriptive text that takes values between 100 and 200 blah blah blah Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.")
	o.setminmaxoccurence(0, 2).settakesparameters(True, "val").setparser(IntParser(100, 200))
	c.addoption(o)
	
	o = CmdLineOption("otherinteger", "o", None).setdescription("This is an integral option with a quite long descriptive text that takes values between 100 and 200")
	o.setminmaxoccurence(0, 2).settakesparameters(True, "int").setparser(IntParser(100, 200))
	c.addoption(o)
	
	o = CmdLineOption("birthdate", "d", "birthdate").setdescription("This is some datetime option")
	o.setminmaxoccurence(0, 1).settakesparameters(True, "birth").setparser(DateTimeParser())
	c.addoption(o)
	
	o = CmdLineOption("protocol", "p", "protocol").setdescription("This is a protocol definition of some kind")
	o.setoccurence(1).settakesparameters(True, "protocol").setparser(EnumParser(set([ "v1", "v2", "legacy" ])))
	c.addoption(o)
	
	o = CmdLineOption("otherstuff", "q", None).setdescription("This is some datetime option")
	o.setminmaxoccurence(0, 1).settakesparameters(True, "start").setparser(ExtendedDateTimeParser())
	c.addoption(o)
	
	o = CmdLineOption("otherstuff2", "r", None).setdescription("This is some other datetime option")
	o.setminmaxoccurence(0, 1).settakesparameters(True, "end").setparser(ExtendedDateTimeParser())
	c.addoption(o)
	
	o = CmdLineOption("verbose", "v", None).setdescription("This option enables verbosity").setminmaxoccurence(0, 3)
	c.addoption(o)

	c.parseordie()


