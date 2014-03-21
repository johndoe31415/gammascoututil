#
#	GammaScoutUtil - Tool to communicate with Gamma Scout Geiger counters.
#	Copyright (C) 2011-2013 Johannes Bauer
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

class TimeAlert():
	def __init__(self, interval = 0):
		self._trigger = None
		self._interval = None
		self.setinterval(interval)
	
	def setinterval(self, interval):
		self._interval = interval
		self.reset()

	def reset(self):
		self._trigger = time.time() + self._interval

	def triggered(self):
		return time.time() > self._trigger
	
	def triggeredreset(self):
		"""Check if alarm has triggered and if so, reset it."""
		result = self.triggered()
		if result:
			self.reset()
		return result

	def getinterval(self):
		return self._interval
