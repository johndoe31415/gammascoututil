#!/usr/bin/python3
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

def expcts(counts):
	(exponent, mantissa) = ((counts[0] & 0xfc) >> 2, ((counts[0] & 0x03) << 8) | counts[1])
	exponent = (exponent + 1) // 2
	if exponent == 0:
		counts = mantissa
	else:
		counts = (mantissa + (2 ** 10)) * (2 ** (exponent - 1))
	return counts


for line in sys.stdin:
	i = int(line)
	cts = [ (i & 0xff00) >> 8, i & 0xff ]
	ects = expcts(cts)
	print(ects)
