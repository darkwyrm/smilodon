'''RetVal is a module for flexible return values and error checking without exceptions'''

# Constants for error checking
OK = ''
NoError = ''

# When either of these are returned and more than one parameter is needed by the function,
# the field 'parameter' will also be returned and will contain the name of the bad parameter
BadParameterValue = 'BadParameterValue'
BadParameterType = 'BadParameterType'
FilesystemError = 'FilesystemError'
ResourceExists = 'ResourceExists'
ResourceNotFound = 'ResourceNotFound'
ExceptionThrown = 'ExceptionThrown'

class RetVal:
	'''The RetVal class enables better error checking and variable return values'''
	def __init__(self, value=OK, info=''):
		self._fields = { '_error':value, '_info':info }
	
	def __contains__(self, key):
		return key in self._fields

	def __delitem__(self, key):
		del self._fields[key]

	def __getitem__(self, key):
		return self._fields[key]
	
	def __iter__(self):
		return self._fields.__iter__()
	
	def __setitem__(self, key, value):
		self._fields[key] = value
	
	def set_error(self, value, info=''):
		'''Sets the error value of the object'''
		self._fields['_error'] = value
		self._fields['_info'] = info

	def error(self):
		'''Gets the error value of the object'''
		return self._fields['_error']

	def set_info(self, value):
		'''Sets the extra error information of the object.'''
		self._fields['_info'] = value

	def info(self):
		'''Gets the error value of the object'''
		return self._fields['_info']

	def set_value(self, name, value):
		'''Adds a field to the object. Returns True if successful.'''
		if name == '_error':
			return False
		
		self._fields[name] = value
		return True

	def set_values(self, values):
		'''Adds multiple dictionary fields to the object. Returns True if successful.'''
		for k,v in values:
			if k in [ '_error', '_info' ]:
				return False
			self._fields[k] = v
		return True
	
	def has_value(self, s):
		'''Tests if a specific value field has been returned'''
		return s in self._fields
	
	def empty(self):
		'''Empties the object of all values and clears any errors'''
		self._fields = { '_error':OK }

	def count(self):
		'''Returns the number of values contained by the return value'''
		return len(self._fields) - 1
	