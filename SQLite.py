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

import sqlite3

class SQLite():
	def __init__(self, filename):
		self._conn = sqlite3.connect(filename)
		self._cursor = self._conn.cursor()

	def commit(self):
		self._conn.commit()

	def execute(self, query, *args):
		self._cursor.execute(query, args)
		return self._cursor.fetchone()

	def exec_mayfail_commit(self, query):
		try:
			self._cursor.execute(query)
			self.commit()
		except sqlite3.OperationalError:
			pass

if __name__ == "__main__":
	s = SQLite("foo.sqlite")
	s.exec_mayfail_commit("CREATE TABLE foo (id integer PRIMARY KEY, bar integer);")
	s.execute("INSERT INTO foo (bar) VALUES (?);", (123))
	s.execute("INSERT INTO foo (bar) VALUES (999);")
	s.commit()
