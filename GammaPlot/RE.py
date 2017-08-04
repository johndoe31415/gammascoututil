#!/usr/bin/python3
#
#	RE - Simple regular expression access object.
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
#	File UUID ff39582a-8d65-4b72-802a-4889cbca3a29

import re

class RE():
	IGNORECASE = re.IGNORECASE

	DECIMAL = "-?[0-9]+"
	FLOAT = DECIMAL + "(?:\\.[0-9]*)?"
	HEXADECIMAL = "(?:0[xX])?[0-9a-fA-F]+"
	ANYNUMBER = "(?:0[xXbo])?[0-9a-fA-F]+"
	IP = DECIMAL + "\\." + DECIMAL + "\\." + DECIMAL + "\\." + DECIMAL 
	STRING = "[^ ]+"
	IDENTIFIER = "[a-zA-Z0-9-_]+"
	
	GFLOAT = "(" + FLOAT + ")"
	GDECIMAL = "(" + DECIMAL + ")"
	GHEXADECIMAL = "(?:0[xX])?([0-9a-fA-F]+)"
	GANYNUMBER = "(" + ANYNUMBER + ")"
	GESCQUOTE = '"((?:\\\\"|[^"])*)"'
	GIP = "(" + IP + ")"
	GSTRING = "(" + STRING + ")"
	GIDENTIFIER = "(" + IDENTIFIER + ")"

	def __init__(self, pattern, **kwargs):
		self._re = re.compile(pattern, flags = kwargs.get("flags", 0))
		self._result = None

	def search(self, text):
		self._result = self._re.search(text)
		if self._result is None:
			return None
		else:
			return self

	def searchall(self, text):
		while True:
			result = self.search(text)
			if result is not None:
				yield result
				text = text[result.end() : ]
			else:
				break
	
	def replaceall(self, text, replacement):
		finding = self.search(text)
		while finding is not None:
			if isinstance(replacement, str):
				repltext = replacement
			else:
				repltext = replacement(self)
			text = text[ : self.start()] + repltext + text[self.end() : ]
			finding = self.search(text)
		return text

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

	def start(self):
		return self._result.start()
	
	def end(self):
		return self._result.end()
	
	def groupdict(self):
		return self._result.groupdict()

	def __getitem__(self, index):
		return self._result.group(index)

if __name__ == "__main__":
	r = RE("foo " + RE.GIP + " bar")
	assert(r.match("foo 192.168.102.99 bar koo")[1] == "192.168.102.99")
	assert(r.match("foo 19231683102399 bar koo") is None)
	assert(RE(RE.GSTRING).match("foobar barfoo")[1] == "foobar")
	assert(RE(RE.GDECIMAL).match("12345 99987")[1] == "12345")
	assert(RE(RE.GFLOAT).match("-1.2345")[1] == "-1.2345")
	assert(RE(RE.GFLOAT).match("-1.2345")[1] == "-1.2345")
	assert(RE(RE.GESCQUOTE).match("\"hallo das ist ja sehr cool\"")[1] == "hallo das ist ja sehr cool")
	assert(RE(RE.GESCQUOTE).match("\"hallo das \\\"ist ja sehr cool\"")[1] == "hallo das \\\"ist ja sehr cool")
	
	r = RE("foo([0-9]+)")
	pattern = "das hier foo93893 ist ein foo1 test foo123 und das hier foo9913 auch"
	for finding in r.searchall(pattern):
		print(finding[1])

	r = RE("foo([0-9]+)")
	pattern = "das hier foo93893 ist ein foo1 test foo123 und das hier foo9913 auch"
	output = r.replaceall(pattern, "replacement")
	print(output)
	
	output = r.replaceall(pattern, lambda x: "bar%smoo" % (x[1]))
	print(output)
