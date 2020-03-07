import clientlib as clib
from shellbase import BaseCommand, gShellCommands

import collections
from glob import glob
import os
import platform
import socket
import subprocess
import sys

from prompt_toolkit import print_formatted_text, HTML

# Special class for handling blanks
class CommandEmpty(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self,rawInput,pTokenList)
		self.name = ''


# Special class for handling anything the shell doesn't support
class CommandUnrecognized(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self,'unrecognized')
		self.name = 'unrecognized'

	def IsValid(self):
		return "Unknown command"

	def Execute(self, pShellState):
		return "Unknown command"


class CommandChDir(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self,rawInput,pTokenList)
		self.name = 'chdir'
		self.helpInfo = 'Usage: cd <location>\nChanges to the specified directory\n\n' + \
						'Aliases: cd'
		self.description = 'change directory/location'

	def GetAliases(self):
		return { "cd":"chdir" }

	def Execute(self, pShellState):
		if (len(self.tokenList) > 0):
			newDir = ''
			if '~' in self.tokenList[0]:
				if platform.system().casefold() == 'windows':
					newDir = self.tokenList[0].replace('~', os.getenv('USERPROFILE'))
				else:
					newDir = self.tokenList[0].replace('~', os.getenv('HOME'))
			else:
				newDir = self.tokenList[0]
			try:
				os.chdir(newDir)
			except Exception as e:
				return e.__str__()

		pShellState.oldpwd = pShellState.pwd
		pShellState.pwd = os.getcwd()

		return ''

	def Autocomplete(self, pTokens):
		if len(pTokens) == 1:
			outData = list()
			
			if pTokens[0][0] == '"':
				quoteMode = True
			else:
				quoteMode = False
			
			if quoteMode:
				items = glob(pTokens[0][1:] + '*')
			else:
				items = glob(pTokens[0] + '*')
			
			for item in items:
				if not os.path.isdir(item):
					continue

				display = item
				if quoteMode or ' ' in item:
					data = '"' + item + '"'
				else:
					data = item
				outData.append([data,display])
					
			return outData
		else:
			return list()


class CommandConnect(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self, rawInput, pTokenList)
		self.name = 'connect'
		self.helpInfo = 'Usage: connect <host> [port=2001]\n' + \
						'Open a connection to a host, optionally specifying a port.\n' + \
						'Aliases: con'
		self.description = 'Connect to a host'

	def Execute(self, pShellState):
		if (len(self.tokenList) > 2):
			print(self.helpInfo)
			return ''

		if pShellState.socket:
			clib.quit(pShellState.sock)
			pShellState.sock = None
		
		if len(self.tokenList) == 2:
			try:
				port_num = int(self.tokenList[1])
			except:
				print("Bad port number %s" % self.tokenList[1])
		else:
			port_num = 2001
		
		out_data = clib.connect(self.tokenList[0], port_num)
		if out_data['error'] == '':
			pShellState.sock = out_data['socket']
			if out_data['version']:
				print("Connected to %s, version %s" % (self.tokenList[0], \
														out_data['version']))
			else:
				print('Connected to host')
		else:
			print(out_data['error'])

		return out_data['error']


class CommandDisconnect(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self, rawInput, pTokenList)
		self.name = 'disconnect'
		self.helpInfo = 'Usage: disconnect <host>\n' + \
						'Close the server connection'
		self.description = 'Disconnect from the host'

	def GetAliases(self):
		return { "quit":"disconnect" }

	def Execute(self, pShellState):
		clib.quit(pShellState.sock)
		return ''


class CommandExit(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self,'exit')
		self.name = 'exit'
		self.helpInfo = 'Usage: exit\nCloses the connection and exits the shell.'
		self.description = 'Exits the shell'

	def GetAliases(self):
		return { "x":"exit", "q":"exit" }

	def Execute(self, shellState):
		if hasattr(shellState,'sock'):
			clib.quit(shellState.sock)
		sys.exit(0)


class CommandHelp(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self,'help')
		self.name = 'help'
		self.helpInfo = 'Usage: help <command>\nProvides information on a command.\n\n' + \
						'Aliases: ?'
		self.description = 'Show help on a command'

	def GetAliases(self):
		return { "?":"help" }

	def Execute(self, shellState):
		if (len(self.tokenList) > 0):
			# help <keyword>
			for cmdName in self.tokenList:
				if (len(cmdName) < 1):
					continue

				if (cmdName in gShellCommands):
					print(gShellCommands[cmdName].GetHelp())
				else:
					print_formatted_text(HTML(
						"No help on <gray><b>%s</b></gray>" % cmdName))
		else:
			# Bare help command: print available commands
			ordered = collections.OrderedDict(sorted(gShellCommands.items()))
			for name,item in ordered.items():
				print_formatted_text(HTML(
					"<gray><b>%s</b>\t%s</gray>" % (name, item.GetDescription())
				))
		return ''


class CommandListDir(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self,rawInput,pTokenList)
		self.name = 'ls'
		self.helpInfo = 'Usage: as per bash ls command or Windows dir command'
		self.description = 'list directory contents'

	def GetAliases(self):
		return { "dir":"ls" }

	def Execute(self, pShellState):
		if sys.platform == 'win32':
			tokens = ['dir','/w']
			tokens.extend(self.tokenList)
			subprocess.call(tokens, shell=True)
		else:
			tokens = ['ls','--color=auto']
			tokens.extend(self.tokenList)
			subprocess.call(tokens)
		return ''

	def Autocomplete(self, pTokens):
		if len(pTokens) == 1:
			outData = list()
			
			if pTokens[0][0] == '"':
				quoteMode = True
			else:
				quoteMode = False
			
			if quoteMode:
				items = glob(pTokens[0][1:] + '*')
			else:
				items = glob(pTokens[0] + '*')
			
			for item in items:
				if not os.path.isdir(item):
					continue

				display = item
				if quoteMode or ' ' in item:
					data = '"' + item + '"'
				else:
					data = item
				outData.append([data,display])
					
			return outData
		else:
			return list()


class CommandLogin(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self, rawInput, pTokenList)
		self.name = 'login'
		self.helpInfo = '''Usage: login <address>
Log into a server once connected. The address used may be the numeric address
(e.g. 557207fd-0a0a-45bb-a402-c38461251f8f) or the friendly address (e.g. 
CatLover). It is not necessary to give the entire workspace address
(CatLover/example.com), but it will not cause any errors if it is. If a
friendly address contains spaces, it must be enclosed in double quotes, as in
"John Q. Public/example.com" or "John Q. Public".'''
		self.description = 'Log into the connected server.'

	def Execute(self, pShellState):
		return 'Unimplemented'


class CommandProfile(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self, rawInput, pTokenList)
		self.name = 'profile'
		self.helpInfo = '''Usage: profile <action> <profilename>
Manage profiles. Actions are detailed below.

create <name> - create a new profile, which is just a name for identification
by the user. The profile may be named anything other than "default", which is
reserved. Profile names are case-sensitive, so "Default" is permitted. Note
that once created, it must be made active and either logging in or
registration is needed for the profile to be useful.

delete <name> - delete a profile and any files associated with it. Because it
cannot be undone, this command requires confirmation from the user.

rename <oldname> <newname> - change the name of a profile. Neither name may be
"default".

list - prints a list of all available profiles

setdefault <name> - sets the profile to be loaded on startup. If only one
profile exists, this action has no effect.

set <name> - activates the specified profile and deactivates the current one.
'''
		self.description = 'Manage profiles.'
			

	def Execute(self, pShellState):
		return 'Unimplemented'


class CommandRegister(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self, rawInput, pTokenList)
		self.name = 'register'
		self.helpInfo = '''Usage: register
Register a new workspace account. This command requires a connection to a
server. Depending on the registration type set on the server, this command may
return a status other than success or failure. If a server immediately creates
a new workspace account, this command will print the new numeric address
created.
'''
		self.description = 'Register a new account on the connected server.'
		

	def Execute(self, pShellState):
		return 'Unimplemented'


class CommandShell(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self,rawInput,pTokenList)
		self.name = 'shell'
		self.helpInfo = 'Usage: shell <command>\n' + \
						'Executes a command directly in the regular user shell.\n' + \
						'Aliases: ` , sh'
		self.description = 'Run a shell command'

	def GetAliases(self):
		return { "sh":"shell", "`":"shell" }

	def Execute(self, pShellState):
		os.system(' '.join(self.tokenList))
		return ''


class CommandUpload(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self, rawInput, pTokenList)
		self.name = 'upload'
		self.helpInfo = 'Usage: upload <filepath> <folder list>\n' + \
						'Upload a file to the specified path'
		self.description = 'Upload a file from the absolute path on the source side to the ' \
							'location relative to the workspace root on the server.'

	def Execute(self, pShellState):
		if (len(self.tokenList) < 2):
			print(self.helpInfo)
			return ''

		path_string = ' '.join(self.tokenList[1:])
		if (clib.exists(pShellState.sock, path_string)) != '':
			print("Unable to find path %s on server" % path_string)

		return ''

