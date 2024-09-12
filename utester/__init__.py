
import mcdreforged.api.all as MCDR

from . import api
from . import commands as CMD

from .api import *

__all__: list[str] = []
__all__.extend(api.__all__)

def on_load(server: MCDR.PluginServerInterface, prev_module):
	server.logger.info('Unit Tester is loading')
	api.on_load(server, prev_module)
	CMD.register(server)

def on_unload(server: MCDR.PluginServerInterface):
	server.logger.info('Unit Tester is unloading')
	api.on_unload(server)
