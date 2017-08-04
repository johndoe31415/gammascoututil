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

import socket
import logging

from GSConnection import GSConnection
from ReaderThreads import SocketReaderThread

class SimulatedConnection(GSConnection):
	def __init__(self, args):
		GSConnection.__init__(self, args)
		self._log = logging.getLogger("gsu.traffic." + self.__class__.__name__)
		self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self._socket.connect(args["device"])
#		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1)
		# TODO: This socket is line-buffered, which is crap. Don't know how to
		# disable the buffering :-(
		self._rxthread = SocketReaderThread(self._socket, self._rxbuf.push)
		self._rxthread.start()
	
	def write(self, data):
		data = data.encode("utf-8")
		self._log.debug("TX %d -> %s" % (len(data), str(data)[1:]))
		self._socket.send(data)

	def close(self):
		self._rxthread.close()
