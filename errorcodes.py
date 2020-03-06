# Class for handling errors. 0 is considered to be a non-error condition.
# The string allows a command to return more specific information about the
# error condition
class CmdError:
	def __init__(self, pCode=0, pString="OK"):
		self.code = pCode
		self.string = pString

ERR_OK = CmdError(0, "OK")
ERR_BAD_DATA = CmdError(1, "Bad data")
ERR_BAD_VALUE = CmdError(2, "Bad value")
ERR_ENTRY_MISSING = CmdError(3, "Entry doesn't exist")
ERR_UNKNOWN_COMMAND = CmdError(4, "Unrecognized command")
ERR_CONNECTION = CmdError(5, "Unable to connect to host")
ERR_NO_SOCKET = CmdError(6, "Couldn't create socket")
ERR_HOST_NOT_FOUND = CmdError(7, 'Host not found')
ERR_CUSTOM = CmdError(255, '')
