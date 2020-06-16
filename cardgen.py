import sys

class Validator:
	'''Abstract class for validating input from the user.'''
	def IsValid(self, data: str):	# pylint: disable=unused-argument
		'''Returns True if data is valid, False if not'''
		return True


class ValueNotEmpty (Validator):
	'''Accepts any non-empty string'''
	def IsValid(self, data: str):
		return bool(data)


class ValueInList (Validator):
	'''Determines if data is in the supplied list'''
	def __init__(self, values: list):
		self.values = values
	
	def IsValid(self, data: str):
		return data in self.values


class IValueInList (Validator):
	'''Determines if data is in the supplied list'''
	def __init__(self, values: list):
		self.values = values
	
	def IsValid(self, data: str):
		return data.casefold() in self.values

class ValueIsInteger (Validator):
	'''Determines if the data is a number'''
	def IsValid(self, data: str):
		try:
			_ = int(data)
		except:
			return False
		return True


def print_usage():
	'''Prints usage information'''
	print("%s: <org|user> <key basename>\nInteractively generate a keycard and associated keys.")

def get_input(prompt, compare=Validator(), default_value=''):
	'''Gets info from the user with an optional default value'''
	value = ''
	while not value:
		value = input(prompt)
		if not value:
			value = default_value
		
		if compare.IsValid(value):
			break
	
	return value.strip()
	

def get_org_info():
	'''Gets all user input for an organization and returns a list of tuples containing it all'''
	out = list()
	out.append(('Name', get_input("Organization Name: ", ValueNotEmpty())))
	out.append(('Street-Address',get_input("Street Address: ", ValueNotEmpty())))
	out.append(('Extended-Address',get_input("Address Line 2: ")))
	out.append(('City',get_input("City: ")))
	out.append(('Province',get_input("Province/State: ")))
	out.append(('Postal-Code',get_input("Postal Code: ")))
	out.append(('Country',get_input("Country: ")))
	
	domain = get_input("Domain: ",ValueNotEmpty())
	out.append(('Domain',domain))
	admin_address = '/'.join(['admin', domain])
	out.append(('Contact-Admin',
				get_input("Administrator contact [%s]: " % admin_address,ValueNotEmpty(),
				admin_address)))
	out.append(('Contact-Abuse',
				get_input("Abuse contact [%s]: " % admin_address,ValueNotEmpty(), admin_address)))
	out.append(('Contact-Support',
				get_input("Support contact [%s]: " % admin_address,ValueNotEmpty(), admin_address)))
	out.append(('Language',get_input("Preferred Language [en]: ", ValueNotEmpty(), 'en')))
	out.append(('Website',get_input("Website URL: ")))

	web_access = 'webmail.' + domain
	out.append(('Web-Access',get_input("Webmail Access [%s]: " % web_access, Validator(),
			web_access)))
	mail_access = 'anselus.' + domain
	out.append(('Anselus-Access',get_input("Anselus Access [%s]: " % mail_access,
			Validator(), mail_access)))
	out.append(('Item-Size-Limit',get_input("Item Size Limit [30MB]: ", ValueIsInteger(), '30')))
	out.append(('Message-Size-Limit',get_input("Message Size Limit [30MB]: ", ValueIsInteger(), 
			'30')))
	out.append(('Time-To-Live',get_input("Cache Update Period (days) [14]: ", ValueIsInteger(), '14')))
	out.append(('Expires',get_input("Time Valid (days) [730]: ", ValueIsInteger(), '730')))

	return out

def generate_org_card(userdata: list):
	'''Generates an organizational keycard from supplied user data'''

def get_user_info():
	'''Gets all user input for a user and returns a list of tuples containing it all'''
	out = list()
	out.append(('Name', get_input("Name (optional, but recommended): ")))
	out.append(('Workspace-Name', get_input(
			"Friendly Anselus Address (optional, but recommended): ")))
	out.append(('Domain', get_input("Domain: ", ValueNotEmpty())))
	return out

def generate_user_card(userdata: list):
	'''Generates a user keycard from supplied user data'''

if __name__ == '__main__':
	if len(sys.argv) < 3 or sys.argv[1].casefold() not in [ 'org', 'user' ]:
		print_usage()
		sys.exit(0)

	cardtype = sys.argv[1].casefold()
	if cardtype == 'org':
		info = get_org_info()
		generate_org_card(info)
	else:
		info = get_user_info()
		generate_user_card(info)
	
	print(info)
