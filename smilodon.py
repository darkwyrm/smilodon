#!/usr/bin/env python3
'''This is the main module'''

import re

from prompt_toolkit import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, ThreadedCompleter

from commandaccess import gCommandAccess
from shellbase import ShellState

class ShellCompleter(Completer):
	'''Class for handling command autocomplete'''
	def __init__(self, pshell_state):
		Completer.__init__(self)
		self.lexer = re.compile(r'"[^"]+"|"[^"]+$|[\S\[\]]+')
		self.shell = pshell_state

	def get_completions(self, document, complete_event):
		tokens = self.lexer.findall(document.current_line_before_cursor.strip())
		
		if len(tokens) == 1:
			commandToken = tokens[0]

			# We have only one token, which is the command name
			names = gCommandAccess.get_command_names()
			for name in names:
				if name.startswith(commandToken):
					yield Completion(name[len(commandToken):],display=name)
		elif tokens:
			cmd = gCommandAccess.get_command(tokens[0])
			if cmd.get_name() != 'unrecognized' and tokens:
				outTokens = cmd.autocomplete(tokens[1:], self.shell)
				for out in outTokens:
					yield Completion(out,display=out,
							start_position=-len(tokens[-1]))
		

class Shell:
	'''The main shell class for the application.'''
	def __init__(self):
		self.state = ShellState()
		
		self.lexer = re.compile(r'"[^"]+"|\S+')

	def Prompt(self):
		'''Begins the prompt loop.'''
		session = PromptSession()
		commandCompleter = ThreadedCompleter(ShellCompleter(self.state))
		while True:
			try:
				rawInput = session.prompt(HTML(
					'🐈<yellow><b> > </b></yellow>' ),
					completer=commandCompleter)
			except KeyboardInterrupt:
				break
			except EOFError:
				break
			else:
				rawTokens = self.lexer.findall(rawInput.strip())
				
				tokens = list()
				for token in rawTokens:
					tokens.append(token.strip('"'))

				if not tokens:
					continue
				
				cmd = gCommandAccess.get_command(tokens[0])
				cmd.set(rawInput)

				returnCode = cmd.execute(self.state)
				if returnCode:
					print(returnCode + '\n')


if __name__ == '__main__':
	Shell().Prompt()
