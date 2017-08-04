#!/usr/bin/python3
#
#	SQLite - Simple SQLite3 abstraction.
#	Copyright (C) 2011-2012 Johannes Bauer
#	
#	This file is part of jpycommon.
#
#	jpycommon is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	jpycommon is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with jpycommon; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>
#
#	File UUID 57f7ef62-5fd2-492d-a8bc-f0039948854a

import sqlite3
import time

class SQLite(object):
	_debug = False
	_debugthreshold = 0.05

	def __init__(self, filename, closecommit = False, detect_types = False, **kwargs):
		self._closecommit = closecommit
		self._commitctr = 0
		if filename is not None:
			if not detect_types:
				self._conn = sqlite3.connect(filename, **kwargs)
			else:
				self._conn = sqlite3.connect(filename, detect_types = sqlite3.PARSE_DECLTYPES, **kwargs)
			self._cursor = self._conn.cursor()

	def cursor(self):
		clone = SQLite(None, self._closecommit)
		clone._conn = self._conn
		clone._cursor = self._conn.cursor()
		return clone

	def close(self):
		if self._closecommit:
			self.commit()
		self._cursor = None
		self._conn.close()

	def __del__(self):
		if self._closecommit:
			self.commit()

	def commit(self):
		self._conn.commit()
	
	def fetchmany(self, howmany = 500):
		return self._cursor.fetchmany(size = howmany)

	def execute(self, query, *args):
		if SQLite._debug:
			t0 = time.time()
		self._cursor.execute(query, args)
		if SQLite._debug:
			t1 = time.time()
			t = t1 - t0
			if t > SQLite._debugthreshold:
				print("Query '%s': %.1f" % (query, t))
		return self

	def execute_autocommit(self, query, *args):
		self._commitctr += 1
		if self._commitctr > 1000:
			self.commit()
			self._commitctr = 0
		return self.execute(query, *args)

	def fetchone(self):
		return self._cursor.fetchone()

	def fetchall(self):
		return self._cursor.fetchall()

	def fetchall_chunks(self, howmany = 500):
		while True:
			chunk = self.fetchmany(howmany)
			if len(chunk) == 0:
				break
			for value in chunk:
				yield value

	def exec_mayfail_commit(self, query, *args):
		try:
			self.execute(query, *args)
			self.commit()
		except sqlite3.OperationalError:
			pass
		except sqlite3.IntegrityError:
			pass

	def getrowid(self):
		return self._cursor.lastrowid

	def insert(self, tablename, fields, **options):
		assert(isinstance(tablename, str))
		assert(isinstance(fields, dict))
		values = ", ".join(([ "?" ] * len(fields)))
		query = "INSERT INTO %s (%s) VALUES (%s);" % (tablename, ", ".join(list(fields.keys())), values)
		return self.execute(query, *list(fields.values()))

if __name__ == "__main__":
	s = SQLite("foo.sqlite")
	s.exec_mayfail_commit("CREATE TABLE foo (id integer PRIMARY KEY, bar integer);")
	s.execute("INSERT INTO foo (bar) VALUES (?);", (123))
	s.execute("INSERT INTO foo (bar) VALUES (999);")
	s.insert("foo", { "bar": 12345 })
	s.commit()

