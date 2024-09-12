
import threading

from typing import TYPE_CHECKING, Callable, Self, TypeAlias
from mcdreforged.api.all import RTextBase, ServerInterface
MessageText: TypeAlias = str | RTextBase

if TYPE_CHECKING:
	from .api import TestCase

__all__ = [
	'Recorder',
]

_ServerInterface_execute = ServerInterface.execute
_ServerInterface_tell = ServerInterface.tell
_ServerInterface_say = ServerInterface.say

class Recorder:
	patched: bool = False
	patch_lock = threading.Lock()

	def __init__(self, test: 'TestCase'):
		self._test = test
		self.executed: list[str] = []
		self.told: list[tuple[str | None, MessageText]] = []
		self.said: list[MessageText] = []
		self._on_execute: Callable[[str], bool | None] | None = None
		self._on_tell: Callable[[str, MessageText], bool | None] | None = None
		self._on_say: Callable[[MessageText], bool | None] | None = None

	def __enter__(self) -> Self:
		return self

	def __exit__(self, exc_typ, exc, exc_trace):
		self.stop()

	@property
	def testcase(self) -> 'TestCase':
		return self._test

	def start(self) -> None:
		with Recorder.patch_lock:
			if Recorder.patched:
				raise RuntimeError('Record patch is already applied')
			Recorder.patched = True
			ServerInterface.execute = self._patch_execute
			ServerInterface.tell = self._patch_tell
			ServerInterface.say = self._patch_say

	def stop(self) -> None:
		with Recorder.patch_lock:
			if not Recorder.patched:
				raise RuntimeError('Record patch had not applied')
			Recorder.patched = False
			ServerInterface.execute = _ServerInterface_execute
			ServerInterface.tell = _ServerInterface_tell
			ServerInterface.say = _ServerInterface_say

	def _patch_execute(recorder, self: ServerInterface, text: str, *, encoding: str | None = None) -> None:
		recorder.executed.append(text)
		if recorder._on_execute is not None and recorder._on_execute(text):
			_ServerInterface_execute(self, text, encoding=encoding)

	def _patch_tell(recorder, self: ServerInterface, player: str, text: MessageText, *, encoding: str | None = None) -> None:
		recorder.told.append((player, text))
		if recorder._on_tell is not None and recorder._on_tell(player, text):
			_ServerInterface_tell(self, player, text, encoding=encoding)

	def _patch_say(recorder, self: ServerInterface, text: MessageText, *, encoding: str | None = None) -> None:
		recorder.told.append((None, text))
		recorder.said.append(text)
		if recorder._on_say is not None and recorder._on_say(text):
			_ServerInterface_say(self, text, encoding=encoding)

	def on_execute(self, cb: Callable[[str], bool | None]) -> Callable[[str], bool | None]:
		self._on_execute = cb
		return cb

	def on_tell(self, cb: Callable[[str, MessageText], bool | None]) -> Callable[[str, MessageText], bool | None]:
		self._on_tell = cb
		return cb

	def on_say(self, cb: Callable[[MessageText], bool | None]) -> Callable[[MessageText], bool | None]:
		self._on_say = cb
		return cb

	def assert_executed(self, commands: str | list[str] | tuple[str], allow_extra: bool = True) -> bool:
		if not isinstance(commands, (list, tuple)):
			commands = (commands, )
		i = 0
		for a in commands:
			while True:
				if i >= len(self.executed):
					return False
				b = self.executed[i]
				i = i + 1
				if a == b:
					break
		return True

	def assert_told_to(self, player: str, messages: MessageText | list[MessageText] | tuple[MessageText], *,
		allow_extra: bool = True, include_say: bool = True
	) -> bool:
		player = player.lower()
		if not isinstance(messages, (list, tuple)):
			messages = (messages, )
		told = [m for p, m in self.told if (include_say if p is None else p.lower() == player)]
		i = 0
		for a in messages:
			while True:
				if i >= len(told):
					return False
				b = told[i]
				i = i + 1
				if isinstance(b, RTextBase):
					if isinstance(a, str):
						if a == b.to_plain_text():
							break
					elif a.to_json_object() == b.to_json_object():
						break
				elif isinstance(a, str) and a == b:
					break
				if not allow_extra:
					return False
		if not allow_extra and len(messages) != len(told):
			return False
		return True

	def assert_said(self, messages: MessageText | list[MessageText] | tuple[MessageText], *, allow_extra: bool = True) -> bool:
		if not isinstance(messages, (list, tuple)):
			messages = (messages, )
		i = 0
		for a in messages:
			while True:
				if i >= len(self.said):
					return False
				b = self.said[i]
				i = i + 1
				if isinstance(b, RTextBase):
					if isinstance(a, str):
						if a == b.to_plain_text():
							break
					elif a.to_json_object() == b.to_json_object():
						break
				elif isinstance(a, str) and a == b:
					break
				if not allow_extra:
					return False
		if not allow_extra and len(messages) != len(self.said):
			return False
		return True
