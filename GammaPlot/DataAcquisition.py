#!/usr/bin/python
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
import time
import datetime
import itertools
import numpy
import matplotlib

from SQLite import SQLite
from DateTimeUtil import DateTimeUtil
from StopWatch import StopWatch

class DataSource():
	def __init__(self):
		pass

	def get(self, fromtimestamp, totimestamp):
		pass

	def dump(self, fromtimestamp = None, totimestamp = None):
		(xfrom, xto, cts) = self.get(fromtimestamp, totimestamp)
		for i in range(len(cts)):
			print("%s   %s   %6.1f" % (xfrom[i], xto[i], cts[i]))

	def integrate(self, fromtimestamp = None, totimestamp = None):
		(xfrom, xto, cts) = self.get(fromtimestamp, totimestamp)
		return sum(cts)
		

class DatabaseDataSource(DataSource):
	def __init__(self, parameters):
		DataSource.__init__(self)
		self._parameters = parameters

	def get(self, fromtimestamp, totimestamp):
		assert(isinstance(fromtimestamp, datetime.datetime))
		assert(isinstance(totimestamp, datetime.datetime))

		t = StopWatch("DataBaseDataSource SQL query")
		db = SQLite(self._parameters["dbfile"] or "gammascout.sqlite")
		points = db.execute("SELECT tfrom, tto, counts FROM data WHERE (tfrom >= ?) AND (tfrom < ?) ORDER BY tfrom ASC;", fromtimestamp, totimestamp).fetchall()
		if len(points) == 0:
			print("Data acquisition returned no points to plotting.")
			sys.exit(1)

		# Parse "from" and "to" from strings to datetime.datetime objects
		xfrom = [ datetime.datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for (x, y, z) in points ]
		xto = [ datetime.datetime.strptime(y, "%Y-%m-%d %H:%M:%S") for (x, y, z) in points ]		
		cts = [ z for (x, y, z) in points ]
		t.finish()
		return (xfrom, xto, cts)

class UniformMockDataSource(DataSource):
	def __init__(self, interval, values):
		DataSource.__init__(self)

		starttime = datetime.datetime(2000, 1, 1, 0, 0, 0)
		interval = datetime.timedelta(0, interval)

		self._xfrom = [ starttime + (i * interval) for i in range(len(values)) ]
		self._xto = [ starttime + ((i + 1) * interval) for i in range(len(values)) ]
		self._cts = values

	def get(self, fromtimestamp = None, totimestamp = None):
		return (self._xfrom, self._xto, self._cts)

class DataAcquisition():
	def __init__(self, parameters, datasource):
		self._parameters = parameters
		fromtimestamp = parameters["starttime"]
		totimestamp = parameters["endtime"]
		assert(isinstance(fromtimestamp, datetime.datetime))
		assert(isinstance(totimestamp, datetime.datetime))

		(self._xfrom, self._xto, self._cts) = datasource.get(fromtimestamp, totimestamp)

		total_plotminutes = DateTimeUtil.deltatosecs(self.gettimerange()) / 60
		print("Acquired data from %s to %s (%d minutes, %d samples)." % (str(self.getfirsttimestamp()), str(self.getlasttimestamp()), total_plotminutes, self.getsamplecount()))

	def rebin(self, bincount = 1000):
		t = StopWatch("Data rebinning of %d to %d bins" % (len(self._cts), bincount))
		destbinsize = self.gettimerangesecs() // bincount

		# Represent input time as float-seconds since start
		xvalues = [ DateTimeUtil.datetimeutc_to_timet(x) for x in self._xfrom ]
		xvalues.append(DateTimeUtil.datetimeutc_to_timet(self._xto[-1]))

		# Integrate Y-values
		yvalues = numpy.array([ 0 ] + self._cts).cumsum()

		new_xvalues = numpy.linspace(xvalues[0], xvalues[-1], bincount + 1)		
		new_binwidth = self.gettimerangesecs() / bincount
		print("Rebinning to binwidth of %.1f sec and %d bins" % (new_binwidth, bincount))
		ecdf = numpy.interp(new_xvalues, xvalues, yvalues)
		
		binyvalues = numpy.diff(ecdf)
		binyvalues /= new_binwidth
		
		binxvalues = new_xvalues[: - 1]
		binxvalues += (new_binwidth // 2)
		binxvalues = [ DateTimeUtil.timet_to_datetimeutc(x) for x in binxvalues ]
		t.finish()

		return (binxvalues, binyvalues, new_binwidth)
	
	def rebintime(self, binseconds = 3600):
		bincount = self.gettimerangesecs() / binseconds
		return self.rebin(bincount)

	def _fillarray(self, x, length):
		prepend = (length - len(x)) // 2
		append = length - len(x) - prepend
		return ([ None ] * prepend) + list(x) + ([ None ] * append)

	def _movingaverage(self, xpts, ypts, ptsperavg):
		result = self._fillarray(matplotlib.mlab.movavg(ypts, ptsperavg), len(xpts))
		return result

	def getplotdata(self):
		(xvalues, yvalues, binwidth) = self.rebin()
		return (xvalues, yvalues)

	def getmovingavgdata(self, avgtimesecs):
		(xvalues, yvalues, binwidth) = self.rebin()
		ptsperavg = round(avgtimesecs / binwidth)
		yvalues = self._movingaverage(xvalues, yvalues, ptsperavg)
		return (xvalues, yvalues)

	def gety(self):
		return self._binyvalues

	def getsamplecount(self):
		return len(self._cts)

	def getfirsttimestamp(self):
		return self._xfrom[0]

	def getlasttimestamp(self):
		return self._xto[-1]

	def gettimerange(self):
		return self.getlasttimestamp() - self.getfirsttimestamp()
	
	def gettimerangesecs(self):
		return DateTimeUtil.deltatosecs(self.gettimerange())

if __name__ == "__main__":
	parameters = {
		"starttime":			datetime.datetime.now(),
		"endtime":				datetime.datetime.now(),
		"resampleinterval":		None,
	}
	s = UniformMockDataSource(1, [ 1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1 ])
	acq = DataAcquisition(parameters, s)

	s.dump()
	print(s.integrate())
	print("-" * 120)
#	acq.dump()
#	print(acq.integrate())
