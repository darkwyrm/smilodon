'''RetVal is a module for flexible return values and error checking without exceptions'''

# Constants for error checking
IsEmpty = 'IsEmpty'
IsNotEmpty = 'IsNotEmpty'
TooSmall = 'TooSmall'
TooLarge = 'TooLarge'

class RetVal:
	'''The RetVal class enables easy error checking and variable return values'''
	def __init__(self):
		self._fields = dict()
		self._fields['_error'] = ''
	
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
	
	def set_value(self, name, value):
		'''Adds a field to the object. Returns True if successful.'''
		if name == '_error':
			return False
		
		self._fields[name] = value
		return True

	def has_value(self, s):
		'''Tests if a specific value field has been returned'''
		return s in self._fields

	def count(self):
		'''Returns the number of values contained by the return value'''
		return len(self._fields) - 1

	def test(self, s):
		'''tests for an error matching the supplied string code'''
		return self._fields['_error'] == s
	