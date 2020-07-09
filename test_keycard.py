'''This module tests the KeyCard class'''
import datetime
import os
import shutil
import time

import nacl.signing

import keycard
from keycard import Base85Encoder
# Pylint doesn't detect the use of this import:
from retval import RetVal # pylint: disable=unused-import

def setup_test(name):
	'''Creates a test folder hierarchy'''
	test_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),'testfiles')
	if not os.path.exists(test_folder):
		os.mkdir(test_folder)

	test_folder = os.path.join(test_folder, name)
	while os.path.exists(test_folder):
		try:
			shutil.rmtree(test_folder)
		except:
			print("Waiting a second for test folder to unlock")
			time.sleep(1.0)
	os.mkdir(test_folder)
	return test_folder


def test_orgcard():
	'''Tests the OrgCard constructor'''
	card = keycard.OrgCard()
	assert card.is_compliant().error(), "Initial OrgCard() complies but shouldn't"

	card.set_fields({
		'Name':'Example, Inc.',
		'Contact-Admin':'admin/example.com',
		'Primary-Signing-Algorithm':'ed25519',
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Encryption-Key-Algorithm':'curve25519',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt'
	})
	rv = card.is_compliant()
	assert rv.error(), "OrgCard() should not comply and did"
	assert rv.info() != 'Missing field Organization-Signature', "Signature complied and shouldn't"


def test_set_fields():
	'''Tests setfields'''
	card = keycard.OrgCard()
	card.set_fields({
		'Name':'Example, Inc.',
		'Street':'1443 Dogwood Lane',
		'City':'Nogales',
		'Province':'AZ',
		'Postal-Code':'85621',
		'Country':'United States',
		'Contact-Admin':'admin/example.com',
		'Language':'English',
		'Website':'https://www.example.com',
		'Primary-Signing-Algorithm':'ed25519',
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Secondary-Signing-Algorithm':'ed25519',
		'Secondary-Signing-Key':'`D7QV39R926R3nf<NjU;pi)80xJxvj#1&iWD0!%6',
		'Encryption-Key-Algorithm':'curve25519',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt',
		'Web-Access':'mail.example.com:2081',
		'Mail-Access':'mail.example.com:2001',
		'Message-Size-Limit':'100MB',
		'noncompliant-field':'foobar2000'
	})
	rv = card.is_compliant()
	assert rv.error(), "Setfield() should not comply and did"
	assert rv.info() != 'Missing field Organization-Signature', "Signature complied and shouldn't"


def test_set_expiration():
	'''Tests set_expiration'''
	card = keycard.UserCard()
	card.set_expiration(7)
	expiration = datetime.datetime.utcnow() + datetime.timedelta(7)
	assert card.fields['Expires'] == expiration.strftime("%Y%m%d"), "Expiration calculations failed"


def test_load_keycard():
	'''Tests keycard loading'''
	test_folder = setup_test('keycard_load')
	
	card = keycard.OrgCard()
	card.set_fields({
		'Type':'Organization',
		'Name':'Example, Inc.',
		'Street':'1443 Dogwood Lane',
		'City':'Nogales',
		'Province':'AZ',
		'Postal-Code':'85621',
		'Country':'United States',
		'Contact-Admin':'admin/example.com',
		'Language':'English',
		'Website':'https://www.example.com',
		'Primary-Signing-Algorithm':'ed25519',
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Secondary-Signing-Algorithm':'ed25519',
		'Secondary-Signing-Key':'`D7QV39R926R3nf<NjU;pi)80xJxvj#1&iWD0!%6',
		'Encryption-Key-Algorithm':'curve25519',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt',
		'Web-Access':'mail.example.com:2081',
		'Mail-Access':'mail.example.com:2001',
		'Message-Size-Limit':'100MB'
	})

	test_card_path = os.path.join(test_folder,'test_card.keycard')
	with open(test_card_path, 'w', newline='\r\n') as f:
		for k,v in card.fields.items():
			f.write("%s:%s\n" % (k,v))

	status = keycard.load_keycard(test_card_path)
	assert not status.error(), "Failed to load test keycard"


def test_orgcard_sign_verify():
	'''Tests the signing of an organizational keycard'''
	test_folder = setup_test('keycard_org_sign_verify')

	skey = nacl.signing.SigningKey.generate()
	ekey = nacl.public.PrivateKey.generate()

	card = keycard.OrgCard()
	card.set_fields({
		'Type':'Organization',
		'Name':'Example, Inc.',
		'Street':'1443 Dogwood Lane',
		'City':'Nogales',
		'Province':'AZ',
		'Postal-Code':'85621',
		'Country':'United States',
		'Contact-Admin':'admin/example.com',
		'Language':'English',
		'Website':'https://www.example.com',
		'Primary-Signing-Algorithm':'ed25519',
		'Primary-Signing-Key':skey.verify_key.encode(Base85Encoder).decode(),
		'Encryption-Key-Algorithm':'curve25519',
		'Encryption-Key':ekey.public_key.encode(Base85Encoder).decode(),
		'Web-Access':'mail.example.com:2081',
		'Mail-Access':'mail.example.com:2001',
		'Message-Size-Limit':'100MB'
	})
	rv = card.sign(skey.encode())
	assert not rv.error(), 'Unexpected RetVal error'
	assert card.signatures['Organization'], 'keycard failed to sign'
	assert card.verify(card.fields['Primary-Signing-Key']), 'keycard failed to verify'

	test_card_path = os.path.join(test_folder, 'test_org_card.keycard')
	rv = card.save(test_card_path)
	assert not rv.error(), "failed to save test keycard"

	rv = keycard.load_keycard(test_card_path)
	assert not rv.error(), "failed to load test keycard"
	testcard = rv['card']
	assert testcard.verify(card.fields['Primary-Signing-Key']), 'test card failed to verify'


def test_usercard():
	'''Tests the UserCard constructor'''
	card = keycard.UserCard()
	rv = card.is_compliant()
	assert rv.error(), "Initial UserCard() complies but shouldn't"

	card.set_fields({
		'Workspace-ID':'00000000-1111-2222-3333-444444444444',
		'Domain':'example.com',
		'Contact-Request-Signing-Algorithm':'ed25519',
		'Contact-Request-Signing-Key':'7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Algorithm':'curve25519',
		'Contact-Request-Encryption-Key':'fbqsEyXT`Sq?us{OgVygsK|zBP7njBmwT+Q_a*0E',
		'Public-Encryption-Algorithm':'curve25519',
		'Public-Encryption-Key':'0IaDFoy}NDe1@fzkg9z!5`@gclY20sRINMJd_{j!',
	})
	card.signatures['User'] = 'TestBadUserSig'
	card.signatures['Organization'] = 'TestBadOrgSig'

	rv = card.is_compliant()
	assert not rv.error(), "UserCard() compliance failed: %s" % rv.info()


def test_usercard_bytestring():
	'''Tests the UserCard get_bytestring() method'''
	card = keycard.UserCard()
	card.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Domain':'example.com',
		'Contact-Request-Signing-Algorithm':'ed25519',
		'Contact-Request-Signing-Key':'7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Algorithm':'curve25519',
		'Contact-Request-Encryption-Key':'yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Algorithm':'curve25519',
		'Public-Encryption-Key':'_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE',
		'Expires':'20201002'
	})

	expected_out = b'Type:User\r\n' \
		b'Name:Corbin Simons\r\n' \
		b'Workspace-ID:4418bf6c-000b-4bb3-8111-316e72030468\r\n' \
		b'Domain:example.com\r\n' \
		b'Contact-Request-Signing-Algorithm:ed25519\r\n' \
		b'Contact-Request-Signing-Key:7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|\r\n' \
		b'Contact-Request-Encryption-Algorithm:curve25519\r\n' \
		b'Contact-Request-Encryption-Key:yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn\r\n' \
		b'Public-Encryption-Algorithm:curve25519\r\n' \
		b'Public-Encryption-Key:_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE\r\n' \
		b'Time-To-Live:7\r\n' \
		b'Expires:20201002\r\n'
	
	assert card.make_bytestring(True) == expected_out, "user byte string didn't match"


def test_usercard_sign():
	'''Tests the signing of a user keycard'''
	skey = nacl.signing.SigningKey(b'{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}', Base85Encoder)
	# crskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)
	# crekey = nacl.public.PrivateKey(b'VyFX5PC~?eL5)>q|6W7ciRrOJw$etlej<tY$f+t_', Base85Encoder)
	# ekey = nacl.public.PrivateKey(b'Wsx6BC(HP~goS-C_`K=6Daqr97kapfc=vQUzi?KI', Base85Encoder)

	card = keycard.UserCard()
	card.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Domain':'example.com',
		'Contact-Request-Signing-Algorithm':'ed25519',
		'Contact-Request-Signing-Key':'7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Algorithm':'curve25519',
		'Contact-Request-Encryption-Key':'yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Algorithm':'curve25519',
		'Public-Encryption-Key':'_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE',
		'Expires':'20201002'
	})
	expected_sig = '#sl4;saPEf*w~PxituHuiXrgP^tko9uO8kib;Wt$>*r(ECw8K;>Uq7zlAWx9%D9HU)`HV87@6Ht5elCJ'
	
	rv = card.sign(skey.encode(), 'User')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert card.signatures['User'], 'keycard failed to user sign'
	assert card.signatures['User'] == expected_sig, "card did not yield the expected signature"


def test_usercard_sign_verify():
	'''Tests the signing of a user keycard'''
	test_folder = setup_test('keycard_user_sign_verify')

	skey = nacl.signing.SigningKey(b'{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}', Base85Encoder)
	# crskey = nacl.signing.SigningKey(b'GS30y3fdJX0H7t&p(!m3oXqlZI1ghz+o!B7Y92Y%', Base85Encoder)
	# crkey = nacl.public.PrivateKey(b'VyFX5PC~?eL5)>q|6W7ciRrOJw$etlej<tY$f+t_', Base85Encoder)
	# ekey = nacl.public.PrivateKey(b'Wsx6BC(HP~goS-C_`K=6Daqr97kapfc=vQUzi?KI', Base85Encoder)

	card = keycard.UserCard()
	card.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Domain':'example.com',
		'Contact-Request-Signing-Algorithm':'ed25519',
		'Contact-Request-Signing-Key':'7dfD==!Jmt4cDtQDBxYa7(dV|N$}8mYwe$=RZuW|',
		'Contact-Request-Encryption-Algorithm':'curve25519',
		'Contact-Request-Encryption-Key':'yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn',
		'Public-Encryption-Algorithm':'curve25519',
		'Public-Encryption-Key':'_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE',
		'Expires':'20201002'
	})

	expected_sig = '#sl4;saPEf*w~PxituHuiXrgP^tko9uO8kib;Wt$>*r(ECw8K;>Uq7zlAWx9%D9HU)`HV87@6Ht5elCJ'

	rv = card.sign(skey.encode(), 'User')
	assert not rv.error(), 'Unexpected RetVal error %s' % rv.error()
	assert card.signatures['User'], 'keycard failed to user sign'
	assert card.signatures['User'] == expected_sig, "card did not yield the expected signature"

	vkey = nacl.signing.VerifyKey(skey.verify_key.encode())

	# This throws an exception if the data doesn't verify
	vkey.verify(card.make_bytestring(1), Base85Encoder.decode(card.signatures['User']))

	rv = card.verify(skey.verify_key.encode(), 'User')
	assert not rv.error(), 'keycard failed to user verify'

	org_skey = nacl.signing.SigningKey(b'JCfIfVhvn|k4Q%M2>@)ENbX%fE_+0Ml2%oz<Mss?',Base85Encoder)
	rv = card.sign(org_skey.encode(), 'Organization')
	assert not rv.error(), 'Unexpected RetVal error'
	assert card.signatures['Organization'], 'keycard failed to org sign'

	rv = card.verify(org_skey.verify_key.encode(), 'Organization')
	assert not rv.error(), 'keycard failed to org verify'

	test_card_path = os.path.join(test_folder, 'test_user_card.keycard')
	rv = card.save(test_card_path)
	assert not rv.error(), "failed to save test keycard"

	rv = keycard.load_keycard(test_card_path)
	assert not rv.error(), "failed to load test keycard"
	testcard = rv['card']

	rv = testcard.verify(skey.verify_key.encode(), 'User')
	assert not rv.error(), 'test keycard failed to user verify'

	rv = testcard.verify(org_skey.verify_key.encode(), 'Organization')
	assert not rv.error(), 'test keycard failed to org verify'
