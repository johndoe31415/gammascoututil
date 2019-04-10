#!/usr/bin/python3
#
#	GammaScoutUtil - Tool to communicate with Gamma Scout Geiger counters.
#	Copyright (C) 2011-2019 Johannes Bauer
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

import collections

class CalibrationData(object):
	_DEFAULT_CALIBRATION_DATA = {
		6050: ("08 04 ab310b00", """
			f3020000fb1de1f68601
			cb2c00000600e6ff7602
			ffffffff5b16acfc6702
			00000000000000000000
			00000000000000000000
			00000000000000000000
			00000000000000000000
			00000000000000000000
		"""),
		7020: ("b0 00 07 7e 00", """
			cd0900001a05f6da2d00
			9a210000c1e1acb12d00
			9a7d00002f0995c63c00
			00a0020002009af24b00
			9a46080004001cc23c00
			c47d130085010e9e2d00
			15dd4400990210b32d00
		"""),
	}
	_CalInterval = collections.namedtuple("CalInterval", [ "xoffset", "c1", "c2", "coeff_linear" ])

	def __init__(self, version = 6900):
		assert(isinstance(version, int))
		self._intervals = [ ]
		self._version = version

	def parse(self, calheader_text, caldata_text):
		calheader_text = calheader_text.split()
		if self._version < 6900:
			range_bits = int(calheader_text[1], 16)
		else:
			range_bits = int(calheader_text[3], 16)

		caldata_text = caldata_text.replace("\r", "")
		caldata_text = caldata_text.replace("\t", "")
		caldata_text = caldata_text.replace(" ", "")
		caldata = caldata_text.strip("\r\n").split("\n")
		caldata = [ bytes.fromhex(line) for line in caldata ]
		for (lineno, line) in enumerate(caldata):
			xoffset = int.from_bytes(line[0 : 4], byteorder = "little")
			c1 = int.from_bytes(line[4 : 6], byteorder = "little") / 256
			c2 = int.from_bytes(line[6 : 8], byteorder = "little")
			coeff_linear = int.from_bytes(line[8 : 10], byteorder = "little")
			if range_bits & (1 << lineno):
				c1 /= 256
			interval = self._CalInterval(xoffset = xoffset, c1 = c1, c2 = c2, coeff_linear = coeff_linear)
			if xoffset > 0:
				self._intervals.append(interval)
		return self

	def _select_interval(self, int_cts):
		if int_cts < self._intervals[0].xoffset:
			return self._intervals[0]
		for (intvl_n, intvl_n1) in zip(self._intervals, self._intervals[1:]):
			if intvl_n.xoffset <= int_cts < intvl_n1.xoffset:
				return intvl_n1
		return self._intervals[-1]

	def _integer_cts_to_usv_per_hr(self, int_cts):
		interval = self._select_interval(int_cts)
		usv_per_hr = interval.coeff_linear * int_cts
		usv_per_hr /= interval.c2 - (interval.c1 * int_cts)
		return usv_per_hr

	def cts_per_sec_to_usv_per_hr(self, cts_per_sec):
		if self._version < 6900:
			return self._integer_cts_to_usv_per_hr(round(cts_per_sec * 64))
		else:
			return self._integer_cts_to_usv_per_hr(round(cts_per_sec * 512))

	@classmethod
	def get_default(cls, version):
		(calheader, caldata) = cls._DEFAULT_CALIBRATION_DATA[version]
		return cls(version = version).parse(calheader, caldata)

if __name__ == "__main__":
	import json
	import gzip

	for caldata_file in [ "testdata_v605.json.gz", "testdata_v702.json.gz" ]:
		with gzip.open(caldata_file, "r") as f:
			testdata = json.load(f)

		calibration = CalibrationData(version = testdata["version"])
		calibration.parse(testdata["caldata"][0], "\n".join(testdata["caldata"][1:]))
		for (counts, expected_dose) in testdata["dose"].items():
			counts = int(counts)
			rate = counts / testdata["interval"]
			calculated_dose = calibration.cts_per_sec_to_usv_per_hr(rate)
			if expected_dose > 0:
				rel_error = (calculated_dose - expected_dose) / expected_dose
				if rel_error > 1e-4:
					print("ERROR: %s %d counts over %d seconds, %.1f cts/sec expected %.5f µSv/hr but calculcated %.5f µSv/hr. Error %.1f%%" % (caldata_file, counts, testdata["interval"], rate, expected_dose, calculated_dose, rel_error * 100))
