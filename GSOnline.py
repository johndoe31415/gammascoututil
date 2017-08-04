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

class GSOnline():
	_intervals = {
		2:			0,
		10:			1,
		30:			2,
		60:			3,
	}
	_revintervals = { value: key for (key, value) in _intervals.items() }

	@staticmethod
	def intervaltime_possible(intervaltime):
		return intervaltime in GSOnline._intervals

	@staticmethod
	def intervaltime_to_cmd(intervaltime):
		return GSOnline._intervals[intervaltime]

	@staticmethod
	def intervalcmd_to_time(intervalcmd):
		return GSOnline._revintervals[intervalcmd]

	@staticmethod
	def possible_interval_str():
		return ", ".join([ str(i) for i in sorted(list(GSOnline._intervals.keys())) ])
