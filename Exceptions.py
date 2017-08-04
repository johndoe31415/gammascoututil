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

class CommunicationException(Exception):
	_errtypes = set([
		"timeout",			# Communication timeout
		"unparsable",		# Unexpected answer
		"feature",			# Missing feature of some sort
	])

	def __init__(self, errtype, errmsg):
		Exception.__init__(self, errmsg)
		if errtype not in CommunicationException._errtypes:
			raise Exception("Unknown errortype '%s'." % (errtype))
		self._errtype = errtype
		self._errmsg = errmsg

	def gettype(self):
		return self._errtype

	def getmsg(self):
		return self._errmsg

	def __str__(self):
		return "Communication failure (%s): %s" % (self.gettype(), self.getmsg())

class InvalidArgumentException(Exception):
	"""Raised when the user specifies an invalid or nonsensical combination of
	arguments on the command line."""
	pass
