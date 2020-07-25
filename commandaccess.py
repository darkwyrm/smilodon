import sys

import shellcommands 

class CommandAccess:
	'''The CommandAccess houses all available command objects'''
	def __init__(self):
		self.aliases = dict()
		self.all_names = list()

		self.add_command(shellcommands.CommandListDir())
		self.add_command(shellcommands.CommandExit())
		self.add_command(shellcommands.CommandHelp())
		self.add_command(shellcommands.CommandShell())

		self.add_command(shellcommands.CommandPreregister())
		self.add_command(shellcommands.CommandProfile())
		self.add_command(shellcommands.CommandRegister())
		self.add_command(shellcommands.CommandSetUserID())

		self.all_names.sort()

	def add_command(self, pCommand):
		'''Add a Command instance to the list'''
		shellcommands.gShellCommands[pCommand.get_name()] = pCommand
		self.all_names.append(pCommand.get_name())
		for k,v in pCommand.get_aliases().items():
			if k in self.aliases:
				print("Error duplicate alias %s. Already exists for %s" %
						(k, self.aliases[k]) )
				sys.exit(0)
			self.aliases[k] = v
			self.all_names.append(k)

	def get_command(self, pName):
		'''Retrives a Command instance for the specified name, including alias resolution.'''
		if len(pName) < 1:
			return shellcommands.CommandEmpty()

		if pName in self.aliases:
			pName = self.aliases[pName]

		if pName in shellcommands.gShellCommands:
			return shellcommands.gShellCommands[pName]

		return shellcommands.CommandUnrecognized()

	def get_command_names(self):
		'''Get the names of all available commands'''
		return self.all_names

gCommandAccess = CommandAccess()
