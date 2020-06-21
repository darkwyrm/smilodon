# pylint: disable=unused-argument,too-many-branches
import collections
from getpass import getpass
from glob import glob
import os
import platform
import subprocess
import sys

from prompt_toolkit import print_formatted_text, HTML

from encryption import check_password_complexity
import helptext
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
		self.helpInfo = helptext.login_cmd
		self.description = 'Log into the connected server.'

	def execute(self, pshell_state):
		# TODO: Implement LOGIN
		return 'Unimplemented'


class CommandProfile(BaseCommand):
	'''User profile management command'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'profile'
		self.helpInfo = helptext.profile_cmd
		self.description = 'Manage profiles.'
	
	def execute(self, pshell_state):
		if len(self.tokenList) == 0:
			print('Active profile: %s' % pshell_state.client.get_active_profile())
			return ''

		verb = self.tokenList[0].casefold()
		if len(self.tokenList) == 1:
			if verb == 'list':
				print("Profiles:")
				profiles = pshell_state.client.get_profiles()
				for profile in profiles:
					print(profile.name)
			else:
				print(self.get_help())
			return ''

		if verb == 'create':
			status = pshell_state.client.create_profile(self.tokenList[1])
			if status.error():
				print("Couldn't create profile: %s" % status.info())
		elif verb == 'delete':
			print("This will delete the profile and all of its files. It can't be undone.")
			choice = input("Really delete profile '%s'? [y/N] " % self.tokenList[1]).casefold()
			if choice in [ 'y', 'yes' ]:
				status = pshell_state.client.delete_profile(self.tokenList[1])
				if status.error():
					print("Couldn't delete profile: %s" % status.info())
				else:
					print("Profile '%s' has been deleted" % self.tokenList[1])
		elif verb == 'set':
			status = pshell_state.client.activate_profile(self.tokenList[1])
			if status.error():
				print("Couldn't activate profile: %s" % status.info())
		elif verb == 'setdefault':
			status = pshell_state.client.set_default_profile(self.tokenList[1])
			if status.error():
				print("Couldn't set profile as default: %s" % status.info())
		elif verb == 'rename':
			if len(self.tokenList) != 3:
				print(self.get_help())
				return ''
			status = pshell_state.client.rename_profile(self.tokenList[1], self.tokenList[2])
			if status.error():
				print("Couldn't rename profile: %s" % status.info())
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
		
		groups = pshell_state.client.get_profiles()
		if len(ptokens) == 2 and ptokens[1] not in groups:
			outdata = [i for i in groups if i.startswith(ptokens[1])]
			return outdata

		return list()


class CommandRegister(BaseCommand):
	'''Register an account on a server'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'register'
		self.helpInfo = helptext.register_cmd
		self.description = 'Register a new account on the connected server.'
		

	def execute(self, pshell_state):
		if len(self.tokenList) != 1:
			print(self.helpInfo)
			return ''
		
		print("Please enter a passphrase. Please use at least 10 characters with a combination" \
			"of uppercase and lowercase letters and preferably a number and/or symbol. You can "
			"even use non-English letters, such as ß, ñ, Ω, and Ç!")
		
		password_needed = True
		while password_needed:
			password = getpass()
			confirmation = getpass("Confirm password: ")
			if password == confirmation:
				status = check_password_complexity(password)
				if status['strength'] in [ 'very weak', 'weak' ]:
					print("Unfortunately, the password you entered was too weak. Please " \
							"use another.")
					continue
				password_needed = False
		
		status = pshell_state.client.register_account(self.tokenList[0], password)
		
		returncodes = {
			304:"This server does not allow self-registration.",
			406:"This server requires payment before registration can be completed.",
			101:"Registration request sent. Awaiting approval.",
			300: "Registration unsuccessful. The server had an error. Please contact technical " \
				"support for the organization for assistance. Sorry!",
			408:"This workspace already exists on the server. Registration is not needed."
		}
		
		if status['code'] == 201:
			# 201 - Registered
			# TODO: finish handling registration
			pass
		elif status['code'] in returncodes.keys():
			return returncodes[status['code']]
		
		return ''


class CommandShell(BaseCommand):
	'''Perform shell commands'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = 'shell'
		self.helpInfo = helptext.shell_cmd
		self.description = 'Run a shell command'

	def get_aliases(self):
		return { "sh":"shell", "`":"shell" }

	def execute(self, pshell_state):
		try:
			os.system(' '.join(self.tokenList))
		except Exception as e:
			print("Error running command: %s" % e)
		return ''
