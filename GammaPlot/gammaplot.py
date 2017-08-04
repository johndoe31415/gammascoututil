#!/usr/bin/python3
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
import numpy
import time
import sqlite3
import datetime
import itertools
import matplotlib.pyplot
import matplotlib.mlab
import matplotlib.dates

from DataAcquisition import DataAcquisition, DatabaseDataSource
from CmdLineParameters import CmdLineParameters

cmdline = CmdLineParameters()
if cmdline["endtime"] < cmdline["starttime"]:
	print("Error: Starrtime (%s) must be before endtime (%s)." % (cmdline["starttime"], cmdline["endtime"]), file = sys.stderr)
	sys.exit(1)

dbdatasrc = DatabaseDataSource(cmdline)
dacq = DataAcquisition(cmdline, dbdatasrc)
(xpts, ypts) = dacq.getplotdata()

plot = matplotlib.pyplot.figure()
subplot = plot.add_subplot(111)

if cmdline["ticktype"] == "day":
	subplot.xaxis.set_major_locator(matplotlib.dates.DayLocator())
	subplot.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m-%d"))
	subplot.xaxis.set_minor_locator(matplotlib.dates.HourLocator())
elif cmdline["ticktype"] == "week":
	subplot.xaxis.set_major_locator(matplotlib.dates.WeekdayLocator(byweekday = matplotlib.dates.MO))
	subplot.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m-%d"))
	subplot.xaxis.set_minor_locator(matplotlib.dates.DayLocator())
elif cmdline["ticktype"] == "month":
	subplot.xaxis.set_major_locator(matplotlib.dates.MonthLocator())
	subplot.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m-%d"))
	subplot.xaxis.set_minor_locator(matplotlib.dates.DayLocator())

subplot.set_xlabel("Time")
subplot.set_ylabel("µSv / h")
if cmdline["origdata"]:
	subplot.plot(xpts, ypts)

if cmdline["avgline"]:
	for avgsecs in cmdline["avgline"]:
		(movavgx, movavgy) = dacq.getmovingavgdata(int(avgsecs))
		if len(movavgx) == len(movavgy):
			subplot.plot(movavgx, movavgy, color = "red", lw = 1, label = "%.0f min" % (avgsecs / 60))
		else:
			print("Binning of %d seconds ignored (too little data to bin)." % (avgsecs))

subplot.set_title("Radiation Intensity over Time")

matplotlib.pyplot.show()



