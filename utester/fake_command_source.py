
from mcdreforged.api.all import (
	MessageText,
	PlayerCommandSource,
	PreferenceItem,
	RTextBase,
)

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
		super(PlayerCommandSource, self).__init__(mcdr_server, info, player):
		super(FakeCommandSource, self).__init__(preference=preference)

class FakeConsoleCommandSource(FakeCommandSource, ConsoleCommandSource):
	def __init__(self, mcdr_server, info, *, preference: PreferenceItem | None = None):
		super(ConsoleCommandSource, self).__init__(mcdr_server, info):
		super(FakeCommandSource, self).__init__(preference=preference)
