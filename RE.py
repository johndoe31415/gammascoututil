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

class RE():
	DECIMAL = "-?[0-9]+"
	HEXADECIMAL = "(?:0[xX])?[0-9a-fA-F]+"
	IP = DECIMAL + "." + DECIMAL + "." + DECIMAL + "." + DECIMAL 
	
	GDECIMAL = "(" + DECIMAL + ")"
	GHEXADECIMAL = "(?:0[xX])?([0-9a-fA-F]+)"
	GESCQUOTE = '"((?:\\\\"|[^"])*)"'
	GIP = "(" + IP + ")"


	def __init__(self, pattern):
		self._re = re.compile(pattern)
		self._result = None

	def search(self, text):
		self._result = self._re.search(text)
		if self._result is None:
			return None
		else:
			return self
	
	def match(self, text):
		self._result = self._re.match(text)
		if self._result is None:
			return None
		else:
			return self

	def getall(self):
		results = [ ]
		for i in range(1, 128):
			try:
				results.append(self._result.group(i))
			except IndexError:
				break
		return results

	def __getitem__(self, index):
		return self._result.group(index)
