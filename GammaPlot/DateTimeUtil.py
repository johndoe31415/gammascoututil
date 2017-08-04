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

import time
import calendar
import datetime

class DateTimeUtil():
	def deltatosecs(timedelta):
		return (timedelta.days * 86400) + timedelta.seconds + (timedelta.microseconds * 1.0e-6)

	def datetimeutc_to_timet(timestamp):
		return calendar.timegm(timestamp.timetuple())

	def timet_to_datetimeutc(timet):
		return datetime.datetime.utcfromtimestamp(timet)

if __name__ == "__main__":
	assert(DateTimeUtil.timet_to_datetimeutc(0) == datetime.datetime(1970, 1, 1, 0, 0, 0))
	assert(DateTimeUtil.timet_to_datetimeutc(3600) == datetime.datetime(1970, 1, 1, 1, 0, 0))
	assert(DateTimeUtil.timet_to_datetimeutc(45296) == datetime.datetime(1970, 1, 1, 12, 34, 56))

	assert(int(DateTimeUtil.datetimeutc_to_timet(datetime.datetime(1970, 1, 1, 0, 0, 0))) == 0)
	assert(int(DateTimeUtil.datetimeutc_to_timet(datetime.datetime(1970, 1, 1, 1, 0, 0))) == 3600)
	assert(int(DateTimeUtil.datetimeutc_to_timet(datetime.datetime(1970, 1, 1, 12, 34, 56))) == 45296)

	year = 2000
	for month in range(1, 13):
		for day in range(1, 31):
			for hour in range(0, 24):
				try:
					tstr = "%04d-%02d-%02d %02d:30:00" % (year, month, day, hour)
#					t1 = datetime.datetime.strptime(tstr, "%Y-%m-%d %H:%M:%S")
					t1 = datetime.datetime(year, month, day, hour, 30, 0)
					t2 = DateTimeUtil.timet_to_datetimeutc(DateTimeUtil.datetimeutc_to_timet(t1))
					print(t1)
					print(t2)
					assert(t1 == t2)
				except ValueError:
					pass


