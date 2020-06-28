'''Provides the command processing API'''
# pylint: disable=unused-argument

from glob import glob
import os
import re

from client import AnselusClient

# This global is needed for meta commands, such as Help. Do not access
# this list directly unless there is literally no other option.
gShellCommands = dict()

# Class for storing the state of the shell
class ShellState:
	'''Stores the state of the shell'''
	def __init__(self):
		self.pwd = os.getcwd()
		if 'OLDPWD' in os.environ:
			self.oldpwd = os.environ['OLDPWD']
		else:
			self.oldpwd = ''
		
		self.aliases = dict()
		self.client = AnselusClient()


# The main base Command class. Defines the basic API and all tagsh commands
# inherit from it
class BaseCommand:
	'''Provides the base API for interacting with Command objects'''
	def parse_input(self, raw_input):
		'''Tokenize the raw input from the user'''
		if len(raw_input) < 1:
			return list()
		
		rawTokens = re.findall(r'"[^"]+"|\S+', raw_input.strip())
		tokens = list()
		for token in rawTokens:
			tokens.append(token.strip('"'))
		return tokens
	
	def set(self, raw_input=None, ptoken_list=None):
		'''Sets the input and does some basic parsing'''
		if not raw_input:
			self.rawCommand = ''
			self.tokenList = list()
		else:
			self.rawCommand = raw_input
			rawTokens = list()
			if ptoken_list is None:
				rawTokens = self.parse_input(raw_input)
			else:
				rawTokens = ptoken_list
			
			if len(rawTokens) > 1:
				self.tokenList = rawTokens[1:]
			else:
				self.tokenList = list()
	
	def __init__(self, raw_input=None, ptoken_list=None):
		self.set(raw_input,ptoken_list)
		if raw_input:
			self.name = raw_input.split(' ')
		self.helpInfo = ''
		self.description = ''
	
	def get_aliases(self):
		'''Returns a dictionary of alternative names for the command'''
		return dict()
	
	def get_help(self):
		'''Returns help information for the command'''
		return self.helpInfo
	
	def get_description(self):
		'''Returns a description of the command'''
		return self.description
	
	def get_name(self):
		'''Returns the command's name'''
		return self.name
	
	def is_valid(self):
		'''Subclasses validate their information and return an error string'''
		return ''
	
	def execute(self, pshell_state):
		'''The base class purposely does nothing. To be implemented by subclasses'''
		return ''
	
	def autocomplete(self, ptokens, pshell_state):
		'''Subclasses implement whatever is needed for their specific case. ptokens 
contains all tokens from the raw input except the name of the command. All 
double quotes have been stripped. Subclasses are expected to return a list 
containing matches.'''
		return list()


class FilespecBaseCommand(BaseCommand):
	'''Many commands operate on a list of file specifiers'''
	def __init__(self, raw_input=None, ptoken_list=None):
		super().__init__(self,raw_input,ptoken_list)
		self.name = 'FilespecBaseCommand'
		
	def ProcessFileList(self, ptoken_list):
		'''Converts a list containing filenames and/or wildcards into a list of file paths.'''
		fileList = list()
		for index in ptoken_list:
			item = index
			
			if item[0] == '~':
				item = item.replace('~', os.getenv('HOME'))
			
			if os.path.isdir(item):
				if item[-1] == '/':
					item = item + "*.*"
				else:
					item = item + "/*.*"
			try:
				if '*' in item:
					result = glob(item)
					fileList.extend(result)
				else:
					fileList.append(item)
			except:
				continue
		return fileList

# This function implements autocompletion for command
# which take a filespec. This can be a directory, file, or 
# wildcard. If a wildcard, we return no results.
def GetFileSpecCompletions(pFileToken):
	'''Implements autocompletion for commands which take a filespec. This 
be a directory, filename, or wildcard. If a wildcard, this method returns no 
results.'''

	if not pFileToken or '*' in pFileToken:
		return list()
	
	outData = list()
	
	if pFileToken[0] == '"':
		quoteMode = True
	else:
		quoteMode = False
	
	if quoteMode:
		items = glob(pFileToken[1:] + '*')
	else:
		items = glob(pFileToken + '*')
	
	for item in items:
		display = item
		if quoteMode or ' ' in item:
			data = '"' + item + '"'
		else:
			data = item
		
		if os.path.isdir(item):
			data = data + '/'
			display = display + '/'
		
		outData.append([data,display])
			
	return outData
