import shellcommands 

import getopt
import os
import re
import sys
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, WordCompleter

class CommandAccess:
	def __init__(self):
		self.aliases = dict()
		self.allNames = list()

		self.AddCommand(shellcommands.CommandListDir())
		self.AddCommand(shellcommands.CommandExit())
		self.AddCommand(shellcommands.CommandHelp())
		self.AddCommand(shellcommands.CommandShell())

		self.AddCommand(shellcommands.CommandConnect())
		self.AddCommand(shellcommands.CommandDisconnect())
		self.AddCommand(shellcommands.CommandLogin())
		self.AddCommand(shellcommands.CommandProfile())
		# Disabled until server support is implemented
		# self.AddCommand(shellcommands.CommandUpload())

		self.allNames.sort()

	def AddCommand(self, pCommand):
		shellcommands.gShellCommands[pCommand.GetName()] = pCommand
		self.allNames.append(pCommand.GetName())
		for k,v in pCommand.GetAliases().items():
			if k in self.aliases:
				print("Error duplicate alias %s. Already exists for %s" %
						(k, self.aliases[k]) )
				sys.exit(0)
			self.aliases[k] = v
			self.allNames.append(k)

	def GetCommand(self, pName):
		if (len(pName) < 1):
			return shellcommands.CommandEmpty()

		if (pName in self.aliases):
			pName = self.aliases[pName]

		if (pName in shellcommands.gShellCommands):
			return shellcommands.gShellCommands[pName]

		return shellcommands.CommandUnrecognized()

	def GetCommandNames(self):
		return self.allNames

gCommandAccess = CommandAccess()
