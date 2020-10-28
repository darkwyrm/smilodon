'''Contains the implementations for shell commands'''
# pylint: disable=unused-argument,too-many-branches
import collections
from getpass import getpass
from glob import glob
import os
import platform
import subprocess
import sys

from prompt_toolkit import print_formatted_text, HTML

from pyanselus.encryption import check_password_complexity
import helptext
from shellbase import BaseCommand, gShellCommands, ShellState

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

	def is_valid(self) -> str:
		return "Unknown command"

	def execute(self, pshell_state: ShellState) -> str:
		return "Unknown command"


class CommandChDir(BaseCommand):
	'''Change directories'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = 'chdir'
		self.helpInfo = 'Usage: cd <location>\nChanges to the specified directory\n\n' + \
						'Aliases: cd'
		self.description = 'change directory/location'

	def get_aliases(self) -> dict:
		return { "cd":"chdir" }

	def execute(self, pshell_state: ShellState) -> str:
		if self.tokenList:
			new_dir = ''
			if '~' in self.tokenList[0]:
				if platform.system().casefold() == 'windows':
					new_dir = self.tokenList[0].replace('~', os.getenv('USERPROFILE'))
				else:
					new_dir = self.tokenList[0].replace('~', os.getenv('HOME'))
			else:
				new_dir = self.tokenList[0]
			try:
				os.chdir(new_dir)
			except Exception as e:
				return e.__str__()

		pshell_state.oldpwd = pshell_state.pwd
		pshell_state.pwd = os.getcwd()

		return ''

	def autocomplete(self, ptokens: list, pshell_state: ShellState):
		if len(ptokens) == 1:
			out_data = list()
			
			quote_mode = bool(ptokens[0][0] == '"')
			if quote_mode:
				items = glob(ptokens[0][1:] + '*')
			else:
				items = glob(ptokens[0] + '*')
			
			for item in items:
				if not os.path.isdir(item):
					continue

				display = item
				if quote_mode or ' ' in item:
					data = '"' + item + '"'
				else:
					data = item
				out_data.append([data,display])
					
			return out_data
		return list()


class CommandExit(BaseCommand):
	'''Exit the program'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,'exit')
		self.name = 'exit'
		self.helpInfo = 'Usage: exit\nCloses the connection and exits the shell.'
		self.description = 'Exits the shell'

	def get_aliases(self) -> dict:
		return { "x":"exit", "q":"exit" }

	def execute(self, pshell_state: ShellState) -> str:
		sys.exit(0)


class CommandHelp(BaseCommand):
	'''Implements the help system'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,'help')
		self.name = 'help'
		self.helpInfo = 'Usage: help <command>\nProvides information on a command.\n\n' + \
						'Aliases: ?'
		self.description = 'Show help on a command'

	def get_aliases(self) -> dict:
		return { "?":"help" }

	def execute(self, pshell_state: ShellState) -> str:
		if self.tokenList:
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

	def get_aliases(self) -> dict:
		return { "dir":"ls" }

	def execute(self, pshell_state: ShellState) -> str:
		if sys.platform == 'win32':
			tokens = ['dir','/w']
			tokens.extend(self.tokenList)
			subprocess.call(tokens, shell=True)
		else:
			tokens = ['ls','--color=auto']
			tokens.extend(self.tokenList)
			subprocess.call(tokens)
		return ''

	def autocomplete(self, ptokens: list, pshell_state: ShellState):
		if len(ptokens) == 1:
			out_data = list()
			
			if ptokens[0][0] == '"':
				quote_mode = True
			else:
				quote_mode = False
			
			if quote_mode:
				items = glob(ptokens[0][1:] + '*')
			else:
				items = glob(ptokens[0] + '*')
			
			for item in items:
				if not os.path.isdir(item):
					continue

				display = item
				if quote_mode or ' ' in item:
					data = '"' + item + '"'
				else:
					data = item
				out_data.append([data,display])
					
			return out_data
		return list()


class CommandPreregister(BaseCommand):
	'''Preregister an account for someone'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'preregister'
		self.helpInfo = helptext.preregister_cmd
		self.description = 'Preregister a new account for someone.'
		
	def execute(self, pshell_state: ShellState) -> str:
		if len(self.tokenList) > 2 or len(self.tokenList) == 0:
			print(self.helpInfo)
			return ''
		
		try:
			port = int(self.tokenList[0])
		except:
			return 'Bad port number'
		
		user_id = ''
		if len(self.tokenList) == 2:
			user_id = self.tokenList[1]
		
		if user_id and ('"' in user_id or '/' in user_id):
			return 'User ID may not contain " or /.'
		
		status = pshell_state.client.preregister_account(port, user_id)
		
		if status['status'] != 200:
			return 'Preregistration error: %s' % (status.info())
		
		outparts = [ 'Preregistration success:\n' ]
		if status['uid']:
			outparts.extend(['User ID: ', status['uid'], '\n'])
		outparts.extend(['Workspace ID: ' , status['wid'], '\n',
						'Registration Code: ', status['regcode']])
		return ''.join(outparts)


class CommandProfile(BaseCommand):
	'''User profile management command'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'profile'
		self.helpInfo = helptext.profile_cmd
		self.description = 'Manage profiles.'
	
	def execute(self, pshell_state: ShellState) -> str:
		if not self.tokenList:
			print('Active profile: %s' % pshell_state.client.get_active_profile_name())
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
	
	def autocomplete(self, ptokens: list, pshell_state: ShellState):
		if len(ptokens) < 1:
			return list()

		verbs = [ 'create', 'delete', 'list', 'rename' ]
		if len(ptokens) == 1 and ptokens[0] not in verbs:
			out_data = [i for i in verbs if i.startswith(ptokens[0])]
			return out_data
		
		groups = pshell_state.client.get_profiles()
		if len(ptokens) == 2 and ptokens[1] not in groups:
			out_data = [i for i in groups if i.startswith(ptokens[1])]
			return out_data

		return list()


class CommandRegister(BaseCommand):
	'''Register an account on a server'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self, raw_input, ptoken_list)
		self.name = 'register'
		self.helpInfo = helptext.register_cmd
		self.description = 'Register a new account on the connected server.'
		

	def execute(self, pshell_state: ShellState) -> str:
		if len(self.tokenList) != 1:
			print(self.helpInfo)
			return ''
		
		print("Please enter a passphrase. Please use at least 10 characters with a combination " \
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
		
		if status.error():
			return 'Registration error %s: %s' % (status.error(), status.info())

		if status['status'] == 201:
			# 201 - Registered

			# TODO: finish handling registration
			# 1) Set friendly name for account, if applicable - SETADDR
			# 2) Upload keycard and receive signed keycard - SIGNCARD
			# 3) Save signed keycard to database
			pass
		elif status['status'] in returncodes.keys():
			return returncodes[status['status']]
		
		return 'Registration success'


class CommandSetInfo(BaseCommand):
	'''Set workspace information'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = 'setinfo'
		self.helpInfo = helptext.setinfo_cmd
		self.description = 'Set workspace information'

	def execute(self, pshell_state: ShellState) -> str:
		# TODO: Implement SETINFO
		return ''


class CommandShell(BaseCommand):
	'''Perform shell commands'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = 'shell'
		self.helpInfo = helptext.shell_cmd
		self.description = 'Run a shell command'

	def get_aliases(self) -> dict:
		'''Return aliases for the command'''
		return { "sh":"shell", "`":"shell" }

	def execute(self, pshell_state: ShellState) -> str:
		try:
			os.system(' '.join(self.tokenList))
		except Exception as e:
			print("Error running command: %s" % e)
		return ''

class CommandSetUserID(BaseCommand):
	'''Sets the workspace's user ID'''
	def __init__(self, raw_input=None, ptoken_list=None):
		BaseCommand.__init__(self,raw_input,ptoken_list)
		self.name = 'setuser_id'
		self.helpInfo = helptext.setuserid_cmd
		self.description = 'Set user id for workspace'

	def execute(self, pshell_state: ShellState) -> str:
		if len(self.tokenList) != 1:
			print(self.helpInfo)
			return ''
		
		if '"' in self.tokenList[0] or "/" in self.tokenList[0]:
			return 'A user id may not contain " or /.'
		
		p = pshell_state.client.get_active_profile()
		worklist = p.get_workspaces()
		user_wksp = None
		for w in worklist:
			if w.type == 'single':
				user_wksp = w
				break
		
		if not user_wksp:
			return "Couldn't find the identity workspace for the profile."
		
		status = user_wksp.set_user_id(self.tokenList[0])
		if status.error():
			return "Error setting user ID %s : %s" % (status.error(), status.info())
		
		return 'Anselus address is now %s/%s' % (user_wksp.uid, user_wksp.domain)
