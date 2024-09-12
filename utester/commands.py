
import mcdreforged.api.all as MCDR

from .api import TestCase

UTesterPrefix = '!!ut'

def register(server: MCDR.PluginServerInterface):
	server.register_command(
		MCDR.Literal(UTesterPrefix).
			then(MCDR.Literal('run').
				then(MCDR.Text('pattern').
					runs(lambda src, ctx: run_tests(src, ctx['pattern'])))).
			then(MCDR.Literal('list').
				then(MCDR.Text('pattern').
					runs(lambda src, ctx: list_tests(src, ctx['pattern']))).
				runs(lambda src, ctx: list_tests(src, ''))))

def run_tests(source: MCDR.CommandSource, pattern: str):
	pat1 = ''
	if '.' in pattern:
		pat1, pattern = pattern.split('.', 1)
	passed, total = 0, 0
	for m, tc in TestCase._avaliable_testcases:
		if pat1 not in m:
			continue
		p, t = tc.do_tests(source, lambda name: pattern in name)
		total = total + t
		passed = passed + p
	source.reply('{} / {} passed'.format(passed, total))

def list_tests(source: MCDR.CommandSource, pattern: str):
	cases = get_testcases(pattern)
	source.reply(MCDR.RText('==== Found {} match tests'.format(len(cases)), color=MCDR.RColor.light_purple))
	for m, n in cases:
		source.reply('{}.{}'.format(m, n))

def get_testcases(pattern: str) -> list[tuple[str, str]]:
	cases = []
	pat1 = ''
	if '.' in pattern:
		pat1, pattern = pattern.split('.', 1)
	for m, tc in TestCase._avaliable_testcases:
		if pat1 not in m:
			continue
		for n, _ in TestCase._testers:
			if pattern in n:
				cases.append((m, n))
	return cases
