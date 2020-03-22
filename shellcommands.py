# pylint: disable=unused-argument,too-many-branches
import collections
from glob import glob
import os
import platform
import subprocess
import sys

from prompt_toolkit import print_formatted_text, HTML

import clientlib as clib
from shellbase import BaseCommand, gShellCommands

class CommandEmpty(BaseCommand):
	'''Special command just to handle blanks'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = ''


class CommandUnrecognized(BaseCommand):
	'''Special class for handling anything the shell doesn't support'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,'unrecognized')
		self.name = 'unrecognized'

	def is_valid(self):
		return "Unknown command"

	def execute(self, pshell_state):
		return "Unknown command"


class CommandChDir(BaseCommand):
	'''Change directories'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = 'chdir'
		self.helpInfo = 'Usage: cd <location>\nChanges to the specified directory\n\n' + \
						'Aliases: cd'
		self.description = 'change directory/location'

	def get_aliases(self):
		return { "cd":"chdir" }

	def execute(self, pshell_state):
		if len(self.tokenList) > 0:
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

		pshell_state.oldpwd = pshell_state.pwd
		pshell_state.pwd = os.getcwd()

		return ''

	def autocomplete(self, ptokens, pshell_state):
		if len(ptokens) == 1:
			outData = list()
			
			quoteMode = bool(ptokens[0][0] == '"')
			if quoteMode:
				items = glob(ptokens[0][1:] + '*')
			else:
				items = glob(ptokens[0] + '*')
			
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
		return list()


class CommandConnect(BaseCommand):
	'''Connect to a server'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'connect'
		self.helpInfo = 'Usage: connect <host> [port=2001]\n' + \
						'Open a connection to a host, optionally specifying a port.\n' + \
						'Aliases: con'
		self.description = 'Connect to a host'

	def execute(self, pshell_state):
		if len(self.tokenList) > 2:
			print(self.helpInfo)
			return ''

		if pshell_state.socket:
			clib.disconnect(pshell_state.sock)
			pshell_state.sock = None
		
		if len(self.tokenList) == 2:
			try:
				port_num = int(self.tokenList[1])
			except:
				print("Bad port number %s" % self.tokenList[1])
		else:
			port_num = 2001
		
		out_data = clib.connect(self.tokenList[0], port_num)
		if out_data['error'] == '':
			pshell_state.sock = out_data['socket']
			if out_data['version']:
				print("Connected to %s, version %s" % (self.tokenList[0], \
														out_data['version']))
			else:
				print('Connected to host')
		else:
			print(out_data['error'])

		return out_data['error']


class CommandDisconnect(BaseCommand):
	'''Disconnect from a server'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'disconnect'
		self.helpInfo = 'Usage: disconnect <host>\n' + \
						'Close the server connection'
		self.description = 'Disconnect from the host'

	def get_aliases(self):
		return { "quit":"disconnect" }

	def execute(self, pshell_state):
		clib.disconnect(pshell_state.sock)
		return ''


class CommandExit(BaseCommand):
	'''Exit the program'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,'exit')
		self.name = 'exit'
		self.helpInfo = 'Usage: exit\nCloses the connection and exits the shell.'
		self.description = 'Exits the shell'

	def get_aliases(self):
		return { "x":"exit", "q":"exit" }

	def execute(self, pshell_state):
		if hasattr(pshell_state,'sock'):
			clib.disconnect(pshell_state.sock)
		sys.exit(0)


class CommandHelp(BaseCommand):
	'''Implements the help system'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,'help')
		self.name = 'help'
		self.helpInfo = 'Usage: help <command>\nProvides information on a command.\n\n' + \
						'Aliases: ?'
		self.description = 'Show help on a command'

	def get_aliases(self):
		return { "?":"help" }

	def execute(self, pshell_state):
		if len(self.tokenList) > 0:
			# help <keyword>
			for cmdName in self.tokenList:
				if len(cmdName) < 1:
					continue

				if cmdName in gShellCommands:
					print(gShellCommands[cmdName].get_help())
				else:
					print_formatted_text(HTML(
						"No help on <gray><b>%s</b></gray>" % cmdName))
		else:
			# Bare help command: print available commands
			ordered = collections.OrderedDict(sorted(gShellCommands.items()))
			for name,item in ordered.items():
				print_formatted_text(HTML(
					"<gray><b>%s</b>\t%s</gray>" % (name, item.get_description())
				))
		return ''


class CommandListDir(BaseCommand):
	'''Performs a directory listing by calling the shell'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = 'ls'
		self.helpInfo = 'Usage: as per bash ls command or Windows dir command'
		self.description = 'list directory contents'

	def get_aliases(self):
		return { "dir":"ls" }

	def execute(self, pshell_state):
		if sys.platform == 'win32':
			tokens = ['dir','/w']
			tokens.extend(self.tokenList)
			subprocess.call(tokens, shell=True)
		else:
			tokens = ['ls','--color=auto']
			tokens.extend(self.tokenList)
			subprocess.call(tokens)
		return ''

	def autocomplete(self, ptokens, pshell_state):
		if len(ptokens) == 1:
			outData = list()
			
			if ptokens[0][0] == '"':
				quoteMode = True
			else:
				quoteMode = False
			
			if quoteMode:
				items = glob(ptokens[0][1:] + '*')
			else:
				items = glob(ptokens[0] + '*')
			
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
		return list()


class CommandLogin(BaseCommand):
	'''Initiates a login.'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'login'
		self.helpInfo = '''Usage: login <address>
Log into a server once connected. The address used may be the numeric address
(e.g. 557207fd-0a0a-45bb-a402-c38461251f8f) or the friendly address (e.g. 
CatLover). It is not necessary to give the entire workspace address
(CatLover/example.com), but it will not cause any errors if used. If a
friendly address contains spaces, it must be enclosed in double quotes, as in
"John Q. Public/example.com" or "John Q. Public".'''
		self.description = 'Log into the connected server.'

	def execute(self, pshell_state):
		return 'Unimplemented'


class CommandProfile(BaseCommand):
	'''User profile management command'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
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
	
	def execute(self, pshell_state):
		if len(self.tokenList) == 0:
			print('Active profile: %s' % pshell_state.fs.get_active_profile())
			return ''

		verb = self.tokenList[0].casefold()
		if len(self.tokenList) == 1:
			if verb == 'list':
				print("Profiles:")
				profiles = pshell_state.fs.get_profiles()
				for profile in profiles:
					print(profile)
			else:
				print(self.get_help())
			return ''

		if verb == 'create':
			status = pshell_state.fs.create_profile(self.tokenList[1])
			if status['error']:
				print("Couldn't create profile: %s" % status['error'])
		elif verb == 'delete':
			print("This will delete the profile and all of its files. It can't be undone.")
			choice = input("Really delete profile %s? [y/N] " % self.tokenList[1]).casefold()
			if choice in [ 'y', 'yes' ]:
				status = pshell_state.fs.delete_profile(self.tokenList[1])
				if status['error']:
					print("Couldn't delete profile: %s" % status['error'])
				else:
					print("Profile '%s' has been deleted" % self.tokenList[1])
		elif verb == 'set':
			status = pshell_state.fs.activate_profile(self.tokenList[1])
			if status['error']:
				print("Couldn't activate profile: %s" % status['error'])
		elif verb == 'setdefault':
			status = pshell_state.fs.set_default_profile(self.tokenList[1])
			if status['error']:
				print("Couldn't set profile as default: %s" % status['error'])
		elif verb == 'rename':
			if len(self.tokenList) != 3:
				print(self.get_help())
				return ''
			status = pshell_state.fs.rename_profile(self.tokenList[1], self.tokenList[2])
			if status['error']:
				print("Couldn't rename profile: %s" % status['error'])
		else:
			print(self.get_help())
		return ''
	
	def autocomplete(self, ptokens, pshell_state):
		if len(ptokens) < 1:
			return list()

		verbs = [ 'create', 'delete', 'list', 'rename' ]
		if len(ptokens) == 1 and ptokens[0] not in verbs:
			outdata = [i for i in verbs if i.startswith(ptokens[0])]
			return outdata
		
		groups = pshell_state.fs.get_profiles()
		if len(ptokens) == 2 and ptokens[1] not in groups:
			outdata = [i for i in groups if i.startswith(ptokens[1])]
			return outdata

		return list()


class CommandRegister(BaseCommand):
	'''Register an account on a server'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'register'
		self.helpInfo = '''Usage: register
Register a new workspace account. This command requires a connection to a
server. Depending on the registration type set on the server, this command may
return a status other than success or failure. If a server immediately creates
a new workspace account, this command will print the new numeric address
created.
'''
		self.description = 'Register a new account on the connected server.'
		

	def execute(self, pshell_state):
		if len(self.tokenList) != 2:
			print(self.helpInfo)
			return ''
		# status = clib.register(pshell_state.sock, self.tokenList[1])


		return 'Unimplemented'


class CommandShell(BaseCommand):
	'''Perform shell commands'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = 'shell'
		self.helpInfo = 'Usage: shell <command>\n' + \
						'executes a command directly in the regular user shell.\n' + \
						'Aliases: ` , sh'
		self.description = 'Run a shell command'

	def get_aliases(self):
		return { "sh":"shell", "`":"shell" }

	def execute(self, pshell_state):
		try:
			os.system(' '.join(self.tokenList))
		except Exception as e:
			print("Error running command: %s" % e)
		return ''


class CommandUpload(BaseCommand):
	'''Uploads a file'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'upload'
		self.helpInfo = 'Usage: upload <filepath> <folder list>\n' + \
						'Upload a file to the specified path'
		self.description = 'Upload a file from the absolute path on the source side to the ' \
							'location relative to the workspace root on the server.'

	def execute(self, pshell_state):
		if len(self.tokenList) < 2:
			print(self.helpInfo)
			return ''

		path_string = ' '.join(self.tokenList[1:])
		if (clib.exists(pshell_state.sock, path_string)) != '':
			print("Unable to find path %s on server" % path_string)

		return ''
