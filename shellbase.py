from glob import glob
import os
import re
import shlex
import sys

import storage

# This global is needed for meta commands, such as Help. Do not access
# this list directly unless there is literally no other option.
gShellCommands = dict()

# Class for storing the state of the shell
class ShellState:
	def __init__(self):
		self.pwd = os.getcwd()
		if ('OLDPWD' in os.environ):
			self.oldpwd = os.environ['OLDPWD']
		else:
			self.oldpwd = ''
		
		self.aliases = dict()
		self.socket = None
		self.fs = storage.ClientStorage()


# The main base Command class. Defines the basic API and all tagsh commands
# inherit from it
class BaseCommand:
	def ParseInput(self, rawInput):
		# This tokenizes the raw input from the user
		if (len(rawInput) < 1):
			return list()
		
		rawTokens = re.findall(r'"[^"]+"|\S+', rawInput.strip())
		tokens = list()
		for token in rawTokens:
			tokens.append(token.strip('"'))
		return tokens
	
	def Set(self, rawInput=None, pTokenList=None):
		# This method merely sets the input and does some basic parsing
		if (rawInput == None or len(rawInput) == 0):
			self.rawCommand = ''
			self.tokenList = list()
		else:
			self.rawCommand = rawInput
			rawTokens = list()
			if (pTokenList == None):
				rawTokens = self.ParseInput(rawInput)
			else:
				rawTokens = pTokenList
			
			if (len(rawTokens) > 1):
				self.tokenList = rawTokens[1:]
			else:
				self.tokenList = list()
	
	def __init__(self, rawInput=None, pTokenList=None):
		self.Set(rawInput,pTokenList)
		if (len(rawInput) > 0):
			self.name = rawInput.split(' ')
		self.helpInfo = ''
		self.description = ''
	
	def GetAliases(self):
		# Returns a dictionary of alternative names for the command
		return dict()
	
	def GetHelp(self):
		# Returns help information for the command
		return self.helpInfo
	
	def GetDescription(self):
		# Returns a description of the command
		return self.description
	
	def GetName(self):
		# Returns the command's name
		return self.name
	
	def IsValid(self):
		# Subclasses validate their information and return an error string
		return ''
	
	def Execute(self, pShellState):
		# The base class purposely does nothing. To be implemented by subclasses
		return ''
	
	def Autocomplete(self, pTokens):
		# Subclasses implement whatever is needed for their specific
		# case. pTokens contains all tokens from the raw input except
		# the name of the command. All double quotes have been stripped.
		# Subclasses are expected to return a list containing matches
		return list()


# Because many commands operate on a list of file specifiers, 
class FilespecBaseCommand(BaseCommand):
	def __init__(self, rawInput=None, pTokenList=None):
		BaseCommand.Set(self,rawInput,pTokenList)
		self.name = 'FilespecBaseCommand'
		
	def ProcessFileList(self, pTokenList):
		# Convert a list containing filenames and/or wildcards into a list
		# of file paths
		fileList = list()
		for index in pTokenList:
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
