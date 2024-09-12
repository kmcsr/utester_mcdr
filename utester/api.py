
import threading

from abc import ABC
from datetime import datetime
from typing import Callable, NoReturn, TypeAlias

from mcdreforged.api.all import (
	CommandSource,
	PluginServerInterface,
	RColor,
	RStyle,
	RText,
	RTextBase,
	ServerInterface,
	PreferenceItem,
)
from mcdreforged.info_reactor.info import Info, InfoSource
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
MessageText: TypeAlias = str | RTextBase

from .fake_command_source import FakeCommandSource, FakePlayerCommandSource, FakeConsoleCommandSource
from .recorder import Recorder

__all__ = [
	'TestCase',
	'TestException', 'TestAssertException',
	'FakeCommandSource', 'FakePlayerCommandSource', 'FakeConsoleCommandSource',
	'Recorder',
]

plugin_interface: PluginServerInterface | None = None

def on_load(server: PluginServerInterface, prev_module):
	plugin_interface = server
	self_plugin_id = server.get_self_metadata().id
	for p in server.get_plugin_list():
		if p != self_plugin_id:
			# Reload plugins to ensure `utester` module instance is up to date
			server.reload_plugin(p)

def on_unload(server: PluginServerInterface):
	plugin_interface = None

class TestCase(ABC):
	_avaliable_testcases: list[tuple[str, 'TestCase']] = []
	_running_test: str | None = None
	_running_test_lock = threading.Lock()

	def __new__(cls, name: str | None = None) -> 'TestCase':
		instance = getattr(cls, '_instance', None)
		if instance is not None:
			return instance
		self = super(TestCase, cls).__new__()
		self._name = name or cls.__name__
		if plugin_interface is None:
			raise RuntimeError('UTester is not loaded!')
		server = ServerInterface.get_instance()
		if server is None:
			raise RuntimeError('ServerInterface is not initialized yet!')
		self._mcdr_server = server._mcdr_server
		plugin = self._mcdr_server.plugin_manager.get_current_running_plugin()
		if plugin is None:
			raise RuntimeError('There are no running plugin in context!')
		if not isinstance(plugin, RegularPlugin):
			raise RuntimeError('Plugin {} is not a RegularPlugin'.format(plugin.get_id()))
		self._plugin = plugin

		self._testers: list[tuple[str, Callable[[TestCase], None]]] = []
		self._current_executor: CommandSource | None = None
		self._verbose_log = False
		self._test_logs: list[tuple[bool, MessageText]] = []
		self._errors: list[Exception] = []

		setattr(cls, '_instance', self)

		plugin_interface.logger.info('Registering test case {}'.format(self.id))
		TestCase._avaliable_testcases.append((self.id, self))

		for n, cb in cls.__dict__.items():
			if n.startswith('test__'):
				self._testers.append((n.removeprefix('test__'), cb))

	def __init_subclass__(cls, name: str | None = None):
		super().__init_subclass__()
		cls()

	@property
	def name(self) -> str:
		return self._name

	@property
	def plugin(self) -> RegularPlugin:
		return self._plugin

	@property
	def plugin_interface(self) -> PluginServerInterface:
		return self.plugin.server_interface

	@property
	def id(self) -> str:
		return '{}:{}'.format(self.plugin.get_id(), self.name)

	@property
	def current_executor(self) -> CommandSource | None:
		return self._current_executor

	def tester(self, cb: Callable[['TestCase'], None]) -> Callable[['TestCase'], None]:
		name = cb.__name__.removeprefix('test__')
		self._testers.append((name, cb))
		return cb

	def _run_tester(self, tester: Callable[['TestCase'], None], *, verbose: bool = False) -> bool | None:
		self._verbose_log = verbose
		self._test_logs.clear()
		self._errors.clear()

		with self._mcdr_server.plugin_manager.with_plugin_context(self.plugin):
			try:
				tester(self)
			except TestException as e:
				if e is SkipTestError:
					return None
				if e is AbortTestError:
					return False
				if len(self._errors) == 0 or e is not self._errors[-1]:
					self.push_error(e)
		if len(self._errors) > 0:
			return False
		return True

	def do_tests(self, source: CommandSource, filter: Callable[[str], bool], *, verbose: bool = False) -> tuple[int, int]:
		self._current_executor = source
		passed, ran = 0, 0
		source.reply(RText('=== {} {} tests'.format(self.id, len(self._testers)), color=RColor.gold, styles=RStyle.italic))
		with TestCase._running_test_lock:
			if TestCase._running_test is not None:
				raise RuntimeError('Test {} is running'.format(TestCase._running_test))
			TestCase._running_test = self.id
		try:
			for name, tester in self._testers:
				res = None
				if filter(name):
					TestCase._running_test = '{}.{}'.format(self.id, name)
					res = self._run_tester(tester, verbose=verbose)
					TestCase._running_test = self.id
				show_all_logs = self._verbose_log
				status: RText
				if res is None:
					status = RText('{} - SKIPPED'.format(name), color=RColor.gray, styles=RStyle.underlined)
				else:
					ran = ran + 1
					if res:
						passed = passed + 1
						status = RText('{} - PASSED'.format(name), color=RColor.green, styles=RStyle.underlined)
					else:
						show_all_logs = True
						status = RText('{} - FAILED'.format(name), color=RColor.red, styles=RStyle.underlined)
				for show, msg in self._test_logs:
					if show_all_logs or show:
						source.reply(msg)
				source.reply(status)
		finally:
			with TestCase._running_test_lock:
				TestCase._running_test = None
		return passed, ran

	def execute_command_by_player(self, player: str, command: str, *,
		date: datetime | None = None,
		preference: PreferenceItem | None = None,
	) -> FakePlayerCommandSource:
		info = self._make_player_info(player, command, date=date)
		source = FakePlayerCommandSource(self._mcdr_server, info, player, preference=preference)
		assert plugin_interface is not None
		plugin_interface.execute_command(command, source)
		return source

	def execute_command_by_console(self, command: str, *, preference: PreferenceItem | None = None) -> FakeConsoleCommandSource:
		info = self._make_console_info(command)
		source = FakeConsoleCommandSource(self._mcdr_server, info, preference=preference)
		assert plugin_interface is not None
		plugin_interface.execute_command(command, source)
		return source

	def _make_player_info(self, player: str, content: str, *, date: datetime | None = None) -> Info:
		date = datetime.now()
		info = Info(InfoSource.SERVER, '[{:02d}:{:02d}:{:02d}] <{}> {}'.format(date.hour, date.minute, date.second, player, content))
		info.hour = date.hour
		info.min = date.minute
		info.sec = date.second
		info.content = content
		info.player = player
		info.logging_level = 'INFO'
		info.attach_mcdr_server(self._mcdr_server)
		return info

	def _make_console_info(self, content: str) -> Info:
		date = datetime.now()
		info = Info(InfoSource.CONSOLE, content)
		info.content = content
		info.attach_mcdr_server(self._mcdr_server)
		return info

	def with_records(self) -> Recorder:
		recorder = Recorder(self)
		return recorder

	def push_error(self, error: Exception) -> None:
		self._errors.append(error)

	def skip(self) -> NoReturn:
		raise SkipTestError

	def abort(self) -> NoReturn:
		raise AbortTestError

	def set_verbose(self) -> None:
		assert self.current_executor
		self._verbose_log = True
		for _, msg in self._test_logs:
			self.current_executor.reply(msg)
		self._test_logs.clear()

	def log(self, message: MessageText, *, force: bool = False) -> None:
		assert self.current_executor
		if self._verbose_log:
			self.current_executor.reply(message)
		else:
			self._test_logs.append((force, message))

	def assert_true(self, got, *, want=True, message: str | None = None, abort: bool = True) -> bool:
		if not got:
			err = TestAssertException(self, want, got, message or 'want True value, got {}'.format(repr(got)))
			self.push_error(err)
			if abort:
				raise err
			return False
		return True

	def assert_false(self, got, *, want=False, message: str | None = None, abort: bool = True) -> bool:
		if got:
			err = TestAssertException(self, want, got, message or 'want False value, got {}'.format(repr(got)))
			self.push_error(err)
			if abort:
				raise err
			return False
		return True

	def assert_is(self, got, want, *, message: str | None = None, abort: bool = True) -> bool:
		return self.assert_true(got is want, want=want, abort=abort, message=message or 'want two same reference')

	def assert_is_not(self, got, want, *, message: str | None = None, abort: bool = True) -> bool:
		return self.assert_true(got is not want, want=want, abort=abort, message=message or 'want two different reference')

	def assert_eq(self, got, want, *, message: str | None = None, abort: bool = True) -> bool:
		return self.assert_true(got == want, want=want, abort=abort, message=message or 'want {}, got {}'.format(want, got))

	def assert_neq(self, got, want, *, message: str | None = None, abort: bool = True) -> bool:
		return self.assert_true(got != want, want=want, abort=abort, message=message or 'not want {}, but got same value'.format(want))

	def assert_lt(self, got, want, *, message: str | None = None, abort: bool = True) -> bool:
		return self.assert_true(got < want, want=want, abort=abort, message=message or 'want less than {}, got {}'.format(want, got))

	def assert_le(self, got, want, *, message: str | None = None, abort: bool = True) -> bool:
		return self.assert_true(got <= want, want=want, abort=abort, message=message or 'want less or equal than {}, got {}'.format(want, got))

	def assert_gt(self, got, want, *, message: str | None = None, abort: bool = True) -> bool:
		return self.assert_true(got > want, want=want, abort=abort, message=message or 'want greater than {}, got {}'.format(want, got))

	def assert_ge(self, got, want, *, message: str | None = None, abort: bool = True) -> bool:
		return self.assert_true(got >= want, want=want, abort=abort, message=message or 'want greater or equal than {}, got {}'.format(want, got))

class TestException(Exception):
	pass

class TestAssertException(TestException):
	def __init__(self, test: TestCase, got, want, message: str):
		super().__init__('Assert failed when testing {}: {}'.format(test.id, message))
		self.testcase = test
		self.want = want
		self.got = got

SkipTestError = TestException('SkipTestError')
AbortTestError = TestException('AbortTestError')
