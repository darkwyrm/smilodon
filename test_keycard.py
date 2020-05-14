'''This module tests the KeyCard class'''
import datetime

import nacl.signing

import keycard
from keycard import Base85Encoder
# Pylint doesn't detect the use of this import:
from retval import RetVal # pylint: disable=unused-import

def test_orgcard():
	'''Tests the OrgCard constructor'''
	card = keycard.OrgCard()
	assert card.is_compliant().error(), "Initial OrgCard() complies but shouldn't"

	card.set_fields({
		'Name':'Example, Inc.',
		'Contact-Admin':'admin/example.com',
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt'
	})
	rv = card.is_compliant()
	assert rv.error(), "OrgCard() should not comply and did"
	assert rv['field'] == 'Organization-Signature', "Signature complied and shouldn't"

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
		'Primary-Signing-Key':'l<V_`qb)QM=K#F>u-GCs?W1+>^nl1*#!%$NRxP-6',
		'Secondary-Signing-Key':'`D7QV39R926R3nf<NjU;pi)80xJxvj#1&iWD0!%6',
		'Encryption-Key':'9+8r$)N}={KFhGD3H2rv<q8$72b4A$K!DN;bGrvt',
		'Web-Access':'mail.example.com:2081',
		'Mail-Access':'mail.example.com:2001',
		'Message-Size-Limit':'100MB',
		'noncompliant-field':'foobar2000'
	})
	rv = card.is_compliant()
	assert rv.error(), "Setfield() should not comply and did"
	assert rv['field'] == 'Organization-Signature', "Signature complied and shouldn't"


def test_set_expiration():
	'''Tests set_expiration'''
	card = keycard.UserCard()
	card.set_expiration(7)
	expiration = datetime.datetime.utcnow() + datetime.timedelta(7)
	assert card.fields['Expires'] == expiration.strftime("%Y%m%d"), "Expiration calculations failed"


def test_orgcard_sign_verify():
	'''Tests the signing of an organizational keycard'''
	skey = nacl.signing.SigningKey.generate()
	ekey = nacl.public.PrivateKey.generate()

	card = keycard.OrgCard()
	card.set_fields({
		'Name':'Example, Inc.',
		'Contact-Admin':'admin/example.com',
		'Primary-Signing-Key':skey.verify_key.encode(Base85Encoder).decode(),
		'Encryption-Key':ekey.public_key.encode(Base85Encoder).decode()
	})
	rv = card.sign(skey.encode())
	assert not rv.error(), 'Unexpected RetVal error'
	assert card.signatures['Organization'], 'keycard failed to sign'
	assert card.verify(card.fields['Primary-Signing-Key']), 'keycard failed to verify'


def test_orgcard_set_from_string():
	'''Tests an organizational keycard from raw text'''
	card = keycard.OrgCard()
	card.set_from_string('''Type:Organization
	Name:Example, Inc.
	Contact-Admin:admin/example.com
	Primary-Signing-Key:fbqsEyXT`Sq?us{OgVygsK|zBP7njBmwT+Q_a*0E
	Encryption-Key:0IaDFoy}NDe1@fzkg9z!5`@gclY20sRINMJd_{j!
	Time-To-Live:30
	Expires:20210507
	Organization-Signature:ct1+I$3hcAikDsXP*%I)z0_9_VH;47DsPd-gsdzbq~LOqq(*1h#R$vC>jz~>_yOk<y4mG}ur^CVFLQ?p
	''')
	assert card.verify(card.fields['Primary-Signing-Key']), 'keycard failed to verify'


def test_usercard():
	'''Tests the UserCard constructor'''
	card = keycard.UserCard()
	rv = card.is_compliant()
	assert rv.error(), "Initial UserCard() complies but shouldn't"

	card.set_fields({
		'Workspace-ID':'00000000-1111-2222-3333-444444444444',
		'Domain':'example.com',
		'Contact-Request-Key':'fbqsEyXT`Sq?us{OgVygsK|zBP7njBmwT+Q_a*0E',
		'Public-Encryption-Key':'0IaDFoy}NDe1@fzkg9z!5`@gclY20sRINMJd_{j!',
	})
	card.signatures['User'] = 'TestBadUserSig'
	card.signatures['Organization'] = 'TestBadOrgSig'

	rv = card.is_compliant()
	assert not rv.error(), "UserCard() compliance failed: %s" % rv['field']


def test_usercard_sign_verify():
	'''Tests the signing of a user keycard'''
	skey = nacl.signing.SigningKey(b'{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}',Base85Encoder)
	crkey = nacl.public.PrivateKey(b'VyFX5PC~?eL5)>q|6W7ciRrOJw$etlej<tY$f+t_',Base85Encoder)
	ekey = nacl.public.PrivateKey(b'Wsx6BC(HP~goS-C_`K=6Daqr97kapfc=vQUzi?KI',Base85Encoder)

	card = keycard.UserCard()
	card.set_fields({
		'Name':'Corbin Simons',
		'Workspace-ID':'4418bf6c-000b-4bb3-8111-316e72030468',
		'Workspace-Name':'csimons/example.com',
		'Domain':'example.com',
		'Contact-Request-Key':crkey.public_key.encode(Base85Encoder).decode(),
		'Public-Encryption-Key':ekey.public_key.encode(Base85Encoder).decode()
	})
	rv = card.sign(skey.encode(Base85Encoder), 'User')
	assert not rv.error(), 'Unexpected RetVal error'
	assert card.signatures['User'], 'keycard failed to user sign'

	org_skey = nacl.signing.SigningKey(b'JCfIfVhvn|k4Q%M2>@)ENbX%fE_+0Ml2%oz<Mss?',Base85Encoder)
	rv = card.sign(org_skey.encode(Base85Encoder), 'Organization')
	assert not rv.error(), 'Unexpected RetVal error'
	assert card.signatures['Organization'], 'keycard failed to org sign'
	
	rv = card.verify(skey.verify_key.encode(Base85Encoder), 'User')
	assert not rv.error(), 'keycard failed to user verify'
	
	rv = card.verify(org_skey.verify_key.encode(Base85Encoder), 'Organization')
	assert not rv.error(), 'keycard failed to org verify'
	print(card)


def test_usercard_set_from_string():
	'''Tests a user keycard from raw text'''
	card = keycard.UserCard()
	card.set_from_string('Type:User\n'
	'Name:Corbin Simons\n'
	'Workspace-ID:4418bf6c-000b-4bb3-8111-316e72030468\n'
	'Workspace-Name:csimons/example.com\n'
	'Domain:example.com\n'
	'Contact-Request-Key:yBZ0{1fE9{2<b~#i^R+JT-yh-y5M(Wyw_)}_SZOn\n'
	'Public-Encryption-Key:_`UC|vltn_%P5}~vwV^)oY){#uvQSSy(dOD_l(yE7\n'
	'Time-To-Live:7\n'
	'Expires:20200812\n'
	'User-Signature:K$&m~?|fdchy4GSTEiCoaF6WxM)ySeV|=#;M35}*wrQ5cSc)CC2l2gY*JF4-vLq(WFg8qE_qks56%nQl\n'
	'Organization-Signature:G(8a}*krMSR($!Uq?=5Sk)J~w2uGGAOD~~<hvsAK7TvS>%>gP{answ=TXB;pakRinUvy1)>B7^4A2tyO\n')
	skey = nacl.signing.SigningKey(b'{Ue^0)?k`s(>pNG&Wg9f5b;VHN1^PC*c4-($G#>}',Base85Encoder)
	org_skey = nacl.signing.SigningKey(b'JCfIfVhvn|k4Q%M2>@)ENbX%fE_+0Ml2%oz<Mss?',Base85Encoder)
	rv = card.verify(skey.verify_key.encode(Base85Encoder), 'User')
	assert rv.error(), "User verify failed in set_from_string"
	rv = card.verify(org_skey.verify_key.encode(Base85Encoder), 'Organization')
	assert rv.error(), "Organization verify failed in set_from_string"


