from __future__ import division

import cmath
import math

from kupfer.objects import Source, Action, TextLeaf
from kupfer import pretty

__kupfer_name__ = _("Calculator")
__kupfer_actions__ = ("Calculate", )
__description__ = _("Calculate expressions starting with '='")
__version__ = ""
__author__ = "Ulrik Sverdrup <ulrik.sverdrup@gmail.com>"

class KupferSurprise (float):
	def __call__(self):
		from kupfer import utils, version
		utils.show_url(version.WEBSITE)
		return self

def format_result(res):
	cres = complex(res)
	parts = []
	if cres.real:
		parts.append(u"%s" % cres.real)
	if cres.imag:
		parts.append(u"%s" % complex(0, cres.imag))
	return u"+".join(parts) or u"%s" % res

class Calculate (Action):
	# since it applies only to special queries, we can up the rank
	rank_adjust = 10
	def __init__(self):
		Action.__init__(self, _("Calculate"))
		self.last_result = None

	def has_result(self):
		return True
	def activate(self, leaf):
		expr = leaf.object.lstrip("= ")
		environment = dict(math.__dict__)
		environment.update(cmath.__dict__)
		# define some constants missing
		if self.last_result:
			environment["_"] = self.last_result
		environment["kupfer"] = KupferSurprise("inf")
		# make the builtins inaccessible
		environment["__builtins__"] = {}
		try:
			result = eval(expr, environment)
			resultstr = format_result(result)
			self.last_result = result
		except Exception, exc:
			pretty.print_error(__name__, type(exc).__name__, exc)
			resultstr = unicode(exc)
		return TextLeaf(resultstr)

	def item_types(self):
		yield TextLeaf
	def valid_for_item(self, leaf):
		text = leaf.object
		return text and text.startswith("=")

	def get_description(self):
		return None