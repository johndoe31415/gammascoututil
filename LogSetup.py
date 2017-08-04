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

import logging

class LogSetup():
	_global_level = {
		0:	logging.ERROR,
		1:	logging.WARN,
		2:	logging.INFO,
		3:	logging.DEBUG,
	}

	def __init__(self, args):
		self._args = args

	def _getloglevel(self):
		lvl = self._args["verbose"]
		if lvl >= 3:
			lvl = 3
		return lvl

	def setup(self):
		lvl = self._getloglevel()
		handler = logging.StreamHandler()
		handler.setLevel(LogSetup._global_level[lvl])
		handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

		facility = logging.getLogger("gsu")
		facility.addHandler(handler)
		facility.setLevel(logging.DEBUG)
			

