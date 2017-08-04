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
import csv
from SQLite import SQLite

class OutputBackend():
	def __init__(self, filename):
		self._filename = filename

	def newinterval(self, fromtime, totime, counts):
		pass

	def close(self):
		pass

class OutputBackendCSV(OutputBackend):
	def __init__(self, filename):
		OutputBackend.__init__(self, filename)
		self._f = open(filename, "w")
		self._csv = csv.writer(self._f)
		self._csv.writerow(["From", "To", "Counts", "Seconds", "CPM", "CPS"])
	
	def newinterval(self, fromtime, totime, counts):
		delta = (totime - fromtime)
		totalseconds = delta.days * 86400 + delta.seconds
		self._csv.writerow([ fromtime.strftime("%Y-%m-%d %H:%M:%S"), totime.strftime("%Y-%m-%d %H:%M:%S"), counts, totalseconds, 60 * counts / totalseconds, counts / totalseconds ])
	
	def close(self):
		self._f.close()

class OutputBackendTXT(OutputBackend):
	def __init__(self, filename):
		OutputBackend.__init__(self, filename)
		self._closeonexit = True
		if filename == "-":
			self._f = sys.stdout
			self._closeonexit = False
		else:
			self._f = open(filename, "w")
		print("%-20s   %-20s   %6s  %6s   %4s   %5s" % ("From", "To", "Counts", "Seconds", "CPM", "CPS"), file = self._f)
		print("-" * 80, file = self._f)
	
	def newinterval(self, fromtime, totime, counts):
		delta = (totime - fromtime)
		totalseconds = delta.days * 86400 + delta.seconds
		print("%-20s   %-20s   %6d   %6d   %4.1f   %5.3f" % (fromtime.strftime("%Y-%m-%d %H:%M:%S"), totime.strftime("%Y-%m-%d %H:%M:%S"), counts, totalseconds, 60 * counts / totalseconds, counts / totalseconds), file = self._f)
	
	def close(self):
		if self._closeonexit:
			self._f.close()

class OutputBackendXML(OutputBackend):
	def __init__(self, filename):
		OutputBackend.__init__(self, filename)
		self._f = open(filename, "w")
		print("<?xml version=\"1.0\" encoding=\"utf-8\" ?>", file = self._f)
		print("<gammascout>", file = self._f)
	
	def newinterval(self, fromtime, totime, counts):
		delta = (totime - fromtime)
		totalseconds = delta.days * 86400 + delta.seconds
		print("	<interval from=\"%s\" to=\"%s\" counts=\"%d\" />" % (fromtime.strftime("%Y-%m-%dT%H:%M:%S"), totime.strftime("%Y-%m-%dT%H:%M:%S"), counts), file = self._f)
	
	def close(self):
		print("</gammascout>", file = self._f)
		self._f.close()

class OutputBackendSqlite(OutputBackend):
	def __init__(self, filename):
		OutputBackend.__init__(self, filename)
		self._db = SQLite(filename)
		self._db.exec_mayfail_commit("""CREATE TABLE data (
			id integer PRIMARY KEY,
			tfrom timestamp NOT NULL,
			tto timestamp NOT NULL,
			counts integer NOT NULL,
			CHECK(tto > tfrom),
			CHECK(counts >= 0)
		);""")

	def newinterval(self, fromtime, totime, counts):
		self._db.execute("INSERT INTO data (tfrom, tto, counts) VALUES (?, ?, ?);", fromtime, totime, counts)
	
	def close(self):
		self._db.commit()

