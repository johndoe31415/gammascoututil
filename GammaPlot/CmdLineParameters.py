from CmdLineParser import CmdLineParser, CmdLineOption
from CmdLineParser import ExtendedDateTimeParser, TimeIntervalParser, EnumParser

class CmdLineParameters():
	def __init__(self):
		self._cmdline = CmdLineParser()

		o = CmdLineOption("starttime", "s", "starttime").setdescription("This is the timestamp at which the plot starts.")
		o.setminmaxoccurence(0, 1).settakesparameters(True, "datetime").setparser(ExtendedDateTimeParser()).setdefaultvalue("now-1M")
		self._cmdline.addoption(o)

		o = CmdLineOption("endtime", "e", "endtime").setdescription("This is the timestamp at which the plot ends.")
		o.setminmaxoccurence(0, 1).settakesparameters(True, "datetime").setparser(ExtendedDateTimeParser()).setdefaultvalue("now")
		self._cmdline.addoption(o)

		o = CmdLineOption("dbfile", "d", "dbfile").setdescription("The filename of the Sqlite3 database which stores the acquired data.")
		o.setminmaxoccurence(0, 1).settakesparameters(True, "filename").setdefaultvalue("gammascout.sqlite")
		self._cmdline.addoption(o)

		o = CmdLineOption("avgline", "a", "avgline").setdescription("Draw a plot average line which averages the described timeinterval. May be specified multiple times in order to get multiple average lines.")
		o.setminmaxoccurence(0, None).settakesparameters(True, "interval").setparser(TimeIntervalParser())
		self._cmdline.addoption(o)

		o = CmdLineOption("ticktype", "t", "ticktype").setdescription("Sets the types of ticks that the X-axis is comprised of.")
		o.setminmaxoccurence(0, 1).settakesparameters(True, "type").setdefaultvalue("week").setparser(EnumParser(set([ "none", "day", "week", "month" ])))
		self._cmdline.addoption(o)

		o = CmdLineOption("origdata", "o").setdescription("Include raw original data in plot. Usually only used for debugging purposes.")
		o.setminmaxoccurence(0, 1)
		self._cmdline.addoption(o)

		self._cmdline.parseordie()

	def __getitem__(self, key):
		return self._cmdline[key]
