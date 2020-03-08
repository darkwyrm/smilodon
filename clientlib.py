'''This module contains the functions needed by any Anselus client for 
communications. Commands largely map 1-to-1 to the commands outlined in the 
spec.'''

import os
import socket
import sys

# Number of seconds to wait for a client before timing out
CONN_TIMEOUT = 900.0

# Size (in bytes) of the read buffer size for recv()
READ_BUFFER_SIZE = 8192

# Write Text
#	Requires: 	valid socket
#				string
#	Returns: [dict] "error" : string
def write_text(sock, text):
	'''Sends a string over a socket'''
	try:
		sock.send(text.encode())
	except Exception as exc:
		sock.close()
		return { 'error' : exc.__str__() }


# Read Text
#	Requires: valid socket
#	Returns: [dict] "error" : string, "string" : string
def read_text(sock):
	'''Reads a string from the supplied socket'''
	try:
		out = sock.recv(READ_BUFFER_SIZE)
	except Exception as exc:
		sock.close()
		return { 'error' : exc.__str__(), 'string' : '' }
	
	try:
		out_string = out.decode()
	except Exception as exc:
		return { 'error' : exc.__str__(), 'string' : '' }
	
	return { 'error' : '', 'string' : out_string }


# Connect
#	Requires: host (hostname or IP)
#	Optional: port number
#	Returns: [dict] socket, IP address, server version (if given), error string
#					
def connect(host, port=2001):
	'''Creates a connection to the server.'''
	out_data = dict()
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# Set a short timeout in case the server doesn't respond immediately,
		# which is the expectation as soon as a client connects.
		sock.settimeout(10.0)
	except:
		return { 'socket' : None, 'error' : "Couldn't create a socket" }
	
	out_data['socket'] = sock
	
	try:
		host_ip = socket.gethostbyname(host)
	except socket.gaierror:
		sock.close()
		return { 'socket' : None, 'error' : "Couldn't locate host %s" % host }
	
	out_data['ip'] = host_ip
	try:
		sock.connect((host_ip, port))
		out_data['error'] = ''
		
		hello = read_text(sock)
		if hello:
			hello = hello['string'].strip().split()
			if len(hello) >= 3:
				out_data['version'] = hello[2]
			else:
				out_data['version'] = ''

	except Exception as exc:
		sock.close()
		return { 'socket' : None, 'error' : "Couldn't connect to host %s: %s" % (host, exc) }

	# Set a timeout of 30 minutes
	sock.settimeout(1800.0)
	return out_data
	
# Disconnect
#	Requires: socket
#	Returns: error string
def disconnect(sock):
	'''Disconnects by sending a QUIT command to the server'''
	# TODO: rewrite to use read_data() and write_data()
	if sock:
		try:
			sock.send('QUIT\r\n'.encode())
		except Exception as exc:
			sock.close()
			return exc.__str__()
	return ''

# Exists
#	Requires: one or more names to describe the path desired
#	Returns: [dict] "exists" : bool, "errorcode" : string, "error" : string
def exists(sock, path):
	'''Checks to see if a path exists on the server side.'''
	try:
		# TODO: rewrite to use read_data() and write_data()
		sock.send(("EXISTS %s\r\n" % path).encode())
		data = sock.recv(8192).decode()
		if data:
			tokens = data.strip().split()
			if tokens[0] == '200':
				return { 'exists' : True, 'error' : '', 'errorcode' : '200' }
	
	except Exception as exc:
		return { 'exists' : False, 'error' : "Failure checking path %s: %s" % (path, exc) }
	
	return {
		'exists' : False,
		'error' : ' '.join(tokens[1:]),
		'errorcode' : tokens[0]
	}

# TODO: Implement login()
# Login
#	Requires: numeric workspace ID
#	Returns: [dict] "errorcode" : string, "error" : string
def login(wid):
	'''Starts the login process by sending the requested workspace ID.'''
	
	return {
		'error' : 'Unimplemented',
		'errorcode' : '301'
	}


# callback for upload() which just prints what it's given
def progress_stdout(value):
	sys.stdout.write("Progress: %s\r" % value)


# TODO: Implement register()
# Register
#	Requires: Nothing
#	Returns: [dict] "devid" : string, "errorcode" : string, "error" : string
def register():
	'''Creates an account on the server.'''
	return {
		'error' : 'Unimplemented',
		'errorcode' : '301'
	}


# Upload
#	Requires:	valid socket
#				local path to file
#				size of file to upload
#				server path to requested destination
#	Optional:	callback function for progress display
#
#	Returns: [dict] error code
#				error string
def upload(sock, path, serverpath, progress):
	'''Upload a local file to the server.'''
	chunk_size = 128

	# Check to see if we're allowed to upload
	filesize = os.path.getsize(path)
	write_text(sock, "UPLOAD %s %s\r\n" % (filesize, serverpath))
	response = read_text(sock)
	if not response['string']:
		# TODO: Properly handle no server response
		raise("No response from server")
	
	if response['string'].strip().split()[0] != 'PROCEED':
		# TODO: Properly handle not being allowed
		print("Unable to upload file. Server response: %s" % response)
		return

	try:
		totalsent = 0
		handle = open(path,'rb')
		data = handle.read(chunk_size)
		while data:
			write_text(sock, "BINARY [%s/%s]\r\n" % (totalsent, filesize))
			sent_size = sock.send(data)
			totalsent = totalsent + sent_size

			if progress:
				progress(float(totalsent / filesize) * 100.0)

			if sent_size < chunk_size:
				break
			
			data = handle.read(chunk_size)
		data.close()
	except Exception as exc:
		print("Failure uploading %s: %s" % (path, exc))
