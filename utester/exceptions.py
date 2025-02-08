
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .api import TestCase

__all__ = [
	'TestException', 'TestAssertException',
	'SkipTestError', 'AbortTestError',
]

class TestException(Exception):
	pass

class TestAssertException(TestException):
	def __init__(self, testcase: 'TestCase', got, want, message: str):
		super().__init__('Assert failed when testing {}: {}'.format(testcase.id, message))
		self.testcase = testcase
		self.want = want
		self.got = got

SkipTestError = TestException('SkipTestError')
AbortTestError = TestException('AbortTestError')
