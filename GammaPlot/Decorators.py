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

import inspect
import functools

class InputParameterException(Exception):
	pass

def typecheck(wrappedfunction):
	"""Checks that all prototype types are satisfied and that the return type
	is satisfied. Throws InputParameterException otherwise."""
	def checkparameter(argname, argvalue, allowedtypes):
		if isinstance(allowedtypes, tuple):
			# Many types are allowed
			checkpassed = False
			for allowedtype in allowedtypes:
				if allowedtype is not None:
					if isinstance(argvalue, allowedtype):
						checkpassed = True
						break
				else:
					if argvalue is None:
						checkpassed = True
						break
			if not checkpassed:
				raise InputParameterException("Argument '%s' must be one of the valid types %s, but is of type %s." % (argname, str(allowedtypes), str(type(argvalue))))
		else:
			# Only one type is allowed
			allowedtype = allowedtypes		
			if not isinstance(argvalue, allowedtype):
				raise InputParameterException("Argument '%s' must be of type %s, but is of type %s." % (argname, str(allowedtype), str(type(argvalue))))


	def typecheckwrapper(*args, **kwargs):
		argspec = inspect.getfullargspec(wrappedfunction)

		for (argname, argvalue) in zip(argspec.args, args):
			if argspec.annotations.get(argname):
				# There is an annotation for this parameter, check if it's valid
				allowedtypes = argspec.annotations.get(argname)
				checkparameter(argname, argvalue, allowedtypes)

		# Do the actual call
		returnvalue = wrappedfunction(*args, **kwargs)

		# If specified, check return type
		if argspec.annotations.get("return") is not None:
			checkparameter("return", returnvalue, argspec.annotations.get("return"))

		return returnvalue	

	functools.update_wrapper(typecheckwrapper, wrappedfunction)
	return typecheckwrapper

