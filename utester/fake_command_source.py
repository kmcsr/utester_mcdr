
from typing import TypeAlias
from mcdreforged.api.all import Info, InfoCommandSource, ConsoleCommandSource, PlayerCommandSource, PreferenceItem, RTextBase
from mcdreforged.info_reactor.info import InfoSource

MessageText: TypeAlias = str | RTextBase

__all__ = [
	'FakeCommandSource', 'FakePlayerCommandSource', 'FakeConsoleCommandSource',
]

class FakeCommandSource:
	def __init__(self, *, preference: PreferenceItem | None = None):
		self.replies: list[MessageText] = []
		self.preference = preference

	@property
	def is_fake(self) -> bool:
		return True

	def get_preference(self) -> PreferenceItem | None:
		return self.preference

	def reply(self, message: MessageText, *, encoding: str | None = None, **kwargs):
		self.replies.append(message)

	def get_reply(self) -> str:
		return '\n'.join(t.to_plain_text() if isinstance(t, RTextBase) else t for t in self.replies)

class FakePlayerCommandSource(FakeCommandSource, PlayerCommandSource):
	def __init__(self, mcdr_server, info, player: str, *, preference: PreferenceItem | None = None):
		PlayerCommandSource.__init__(self, mcdr_server, info, player)
		FakeCommandSource.__init__(self, preference=preference)

class FakeConsoleCommandSource(FakeCommandSource, ConsoleCommandSource):
	def __init__(self, mcdr_server, info, *, preference: PreferenceItem | None = None):
		ConsoleCommandSource.__init__(self, mcdr_server, info)
		FakeCommandSource.__init__(self, preference=preference)

class FakeInfo(Info):
	def __init__(self, source: InfoSource, raw_content: str):
		super().__init__(source, raw_content)
		self._command_source: InfoCommandSource | None = None

	def get_command_source(self) -> InfoCommandSource | None:
		return self._command_source
