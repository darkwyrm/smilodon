'''This module contains the functions needed by any Anselus client for 
communications. Commands largely map 1-to-1 to the commands outlined in the 
spec.'''

from base64 import b85decode
import os
import socket
import sys
import time
import uuid

import nacl.pwhash
import nacl.secret

import utils

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

# Read Response
#	Requires: valid socket
#	Returns: [dict] "error" : string, "errorcode" : int
def read_response(sock):
	'''Reads a server response and returns a separated code and string'''
	
	response = read_text(sock)
	if response['error']:
		return { 'error' : response['error'], 'errorcode' : 0 }
	
	try:
		error_code = int(response['string'][0:3])
	except:
		return { 'error' : response['error'], 'errorcode' : 0 }
	
	return { 'errorcode' : error_code, 'error' : response['error'] }

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
	
# Device
#	Requires: device ID, session string
#	Returns: [dict] "errorcode" : int, "error" : string
def device(sock, devid, session_str):
	'''Completes the login process by submitting device ID and its session string.'''
	if not utils.validate_uuid(devid):
		return {
			'error' : 'BAD REQUEST',
			'errorcode' : 400
		}

	response = write_text(sock, 'DEVICE %s %s\r\n' % (devid, session_str))
	if not response['error']:
		return response
	
	return read_response(sock)


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
#	Returns: [dict] "exists" : bool, "errorcode" : int, "error" : string
def exists(sock, path):
	'''Checks to see if a path exists on the server side.'''
	try:
		# TODO: rewrite to use read_data() and write_data()
		sock.send(("EXISTS %s\r\n" % path).encode())
		data = sock.recv(8192).decode()
		if data:
			tokens = data.strip().split()
			if tokens[0] == '200':
				return { 'exists' : True, 'error' : '', 'errorcode' : 200 }
	
	except Exception as exc:
		return { 'exists' : False, 'error' : "Failure checking path %s: %s" % (path, exc) }
	
	return {
		'exists' : False,
		'error' : ' '.join(tokens[1:]),
		'errorcode' : tokens[0]
	}

# Login
#	Requires: numeric workspace ID
#	Returns: [dict] "errorcode" : int, "error" : string
def login(sock, wid):
	'''Starts the login process by sending the requested workspace ID.'''
	if not utils.validate_uuid(wid):
		return {
			'error' : 'BAD REQUEST',
			'errorcode' : 400
		}

	response = write_text(sock, 'LOGIN %s\r\n' % wid)
	if not response['error']:
		return response
	
	return read_response(sock)

# Password
#	Requires: workspace ID, password string
#	Returns: [dict] "errorcode" : int, "error" : string
def password(sock, wid, pword):
	'''Continues the login process by hashing a password and sending it to the server.'''
	if not password or not utils.validate_uuid(wid):
		return {
			'error' : 'BAD REQUEST',
			'errorcode' : 400
		}
	
	# The server will salt the hash we submit, but we'll salt anyway with the WID for extra safety.
	pwhash = nacl.pwhash.argon2id.kdf(nacl.secret.SecretBox.KEY_SIZE,
							bytes(pword, 'utf8'), wid,
							opslimit=nacl.pwhash.argon2id.OPSLIMIT_INTERACTIVE,
							memlimit=nacl.pwhash.argon2id.MEMLIMIT_INTERACTIVE)	
	response = write_text(sock, 'PASSWORD %s\r\n' % pwhash)
	if not response['error']:
		return response
	
	return read_response(sock)


# Register
#	Requires: valid socket, password
#	Returns: [dict] "wid": string, "devid" : string, "session" : string, "errorcode" : int,
# 			"error" : string
def register(sock, pword):
	'''Creates an account on the server.'''
	
	# This construct is a little strange, but it is to work around the minute possibility that
	# there is a WID collision, i.e. the WID generated by the client already exists on the server.
	# In such an event, it should try again. However, in the ridiculously small chance that the 
	# client keeps generating collisions, it should wait 3 seconds after 10 collisions to reduce 
	# server load.
	devid = ''
	wid = ''
	response = dict()
	tries = 1
	while not devid:
		if not tries % 10:
			time.sleep(3.0)
		
		wid = str(uuid.uuid4())
		pwhash = nacl.pwhash.argon2id.kdf(nacl.secret.SecretBox.KEY_SIZE,
								bytes(pword, 'utf8'), wid,
								opslimit=nacl.pwhash.argon2id.OPSLIMIT_INTERACTIVE,
								memlimit=nacl.pwhash.argon2id.MEMLIMIT_INTERACTIVE)	
		response = write_text(sock, 'REGISTER %s %s\r\n' % (wid, pwhash))
		if response['error']:
			return response
		
		response = read_response(sock)
		if response['errorcode'] in [ 304, 406 ]:	# Registration closed, Payment required
			break
		elif response['errorcode'] in [ 101, 201]:	# Pending, Success
			tokens = response['error'].split()
			if len(tokens) != 2 or not utils.validate_uuid(tokens[0]):
				return { 'errorcode' : 300, 'error' : 'INTERNAL SERVER ERROR' }
			response['wid'] = wid
			response['devid'] = tokens[0]
			response['session'] = tokens[1]
			break
		elif response['errorcode'] == 408:	# WID exists
			tries = tries + 1
		else:
			# Something we didn't expect
			break
	
	return response


# callback for upload() which just prints what it's given
def progress_stdout(value):
	sys.stdout.write("Progress: %s\r" % value)


# TODO: Refactor/update to match current spec
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
