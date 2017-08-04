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

class DosisConversion():
	@staticmethod
	def cts_per_min_to_usv_per_hr(cts_per_min):
		"""Calibration curves of the Gamma Scout to convert counts per minute
		to µSv per hour. Only valid for Gamma Scout tubes (LND 712)."""
		if cts_per_min <= 110:
			coefficient = 138.3
		elif cts_per_min <= 388:
			coefficient = -0.08339350180505416 * cts_per_min + 147.56
		elif cts_per_min <= 1327:
			coefficient = -0.01931769722814499 * cts_per_min + 122.5
		elif cts_per_min <= 4513:
			coefficient = -0.004583987441130298 * cts_per_min + 102.65
		else:
			coefficient = -0.0009384033800311318 * cts_per_min + 85.706
		return cts_per_min / coefficient

	@staticmethod
	def cts_per_sec_to_usv_per_hr(cts_per_sec):
		return DosisConversion.cts_per_min_to_usv_per_hr(60 * cts_per_sec)

if __name__ == "__main__":
#	for cts_per_min in range(3000):
#		usv_per_hr = DosisConversion.cts_per_min_to_usv_per_hr(cts_per_min)
#		print("%-3d %.3f" % (cts_per_min, usv_per_hr))

	cts_per_min = 1
	while cts_per_min < 10e3:
		usv_per_hr = DosisConversion.cts_per_min_to_usv_per_hr(cts_per_min)
		naive_usv_per_hr = cts_per_min / 76.4
		error = (naive_usv_per_hr - usv_per_hr) / usv_per_hr
		print("%.4f %.4f %.4f %.4f" % (cts_per_min, usv_per_hr, naive_usv_per_hr, 100 * error))
		cts_per_min *= 1.005

#	for cts_per_min in [ 200, 400, 800, 1000, 2000, 3000, 4000, 5000, 6000 ]:
#		usv_per_hr = DosisConversion.cts_per_min_to_usv_per_hr(cts_per_min)
#		print("%-3d %.3f" % (cts_per_min, usv_per_hr))

