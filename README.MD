
# UTester

This is a unit test framework for MCDReforged plugins

## How to use

Example project structure
```
{plugin_id}/
  __init__.py
  ... .py
  _utester/
  	__init__.py
    testcase1.py
    ... .py
```

In `{plugin_id}/__init__.py`
```py
...

def on_load(server: PluginServerInterface) -> None:
	... # do some setup process

	server.register_command(Literal('!!hello').runs(reply_hello))

	from . import _utester

def reply_hello(source: CommandSource) -> None:
	if isinstance(source, PlayerCommandSource):
		source.reply(f'Hello {source.player} ^.^')
	else:
		source.reply('Hello unknown person')

```

In `_utester/__init__.py`
```py
try:
	import utester
except ModuleNotFoundError:
	pass
else:
	from . import testcase1
	from . import testcase2
	...
```
We check if `utester` is loaded by MCDReforge (if not loaded it will raise `ModuleNotFoundError`), instead of put it into hard required depencies.  
`utester` will automatically reload those plugins already loaded before it, so no need to worry about the loading sequence.

In `testcase1.py`
```py
import utester

class TestCase1(utester.TestCase):
	def test__command_hello_by_player(self):
		source = self.execute_command_by_player('Alex', '!!hello')
		self.assert_eq(source.get_reply(), 'Hello Alex ^.^')

	def test__command_hello_by_console(self):
		source = self.execute_command_by_console('!!hello')
		self.assert_eq(source.get_reply(), 'Hello unknown person')
```
There is no need for manually initializing `TestCase`s after define it, since we already did that by `__init_subclass__` hook.  
Methods begins with `test__` will automatically registered as tester functions when initializing.

You can also register tester by using the `tester` function wrapper, e.g.
```py
import utester

class TestCase1(utester.TestCase):
	pass

testcast1 = TestCase1()

@testcast1.tester
def command_hello_by_player(tc):
	source = tc.execute_command_by_player('Alex', '!!hello')
	tc.assert_eq(source.get_reply(), 'Hello Alex ^.^')

@testcast1.tester
def command_hello_by_console(tc):
	source = tc.execute_command_by_console('!!hello')
	tc.assert_eq(source.get_reply(), 'Hello unknown person')
```  

