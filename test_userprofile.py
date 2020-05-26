import os

from userprofile import Profile
import userprofile

def setup_test(name):
	'''Creates a new profile folder hierarchy'''
	test_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)),'testfiles')
	if not os.path.exists(test_folder):
		os.mkdir(test_folder)

	profiletest_folder = os.path.join(test_folder, name)
	if not os.path.exists(profiletest_folder):
		os.mkdir(profiletest_folder)
	
	return profiletest_folder

def test_profile_class():
	'''Test the Profile class. It's not big or complicated, so several 
	tests are grouped together into one'''

	#profile_test_folder = setup_test('profile_class')
	profile = Profile()
	profile.name = 'Primary'
	profile.id = 'ca7149eb-e533-4de6-90b1-3b0181d6fa16'
	profile.wid = 'b5a9367e-680d-46c0-bb2c-73932a6d4007'
	profile.domain = 'example.com'

	# Most of the class is so simple that it doesn't really need test
	# coverage, but set_from_dict and as_dict are a bit more than that.
	test_dict = {
		'name' : 'Primary',
		'isdefault' : False,
		'id' : 'ca7149eb-e533-4de6-90b1-3b0181d6fa16',
		'wid' : 'b5a9367e-680d-46c0-bb2c-73932a6d4007',
		'domain' : 'example.com',
		'port' : 2001
	}
	assert profile.as_dict() == test_dict, "Output did not match test data"

	profile = Profile()
	profile.set_from_dict(test_dict)
	assert 	profile.name == 'Primary' and \
			profile.isdefault == False and \
			profile.id == 'ca7149eb-e533-4de6-90b1-3b0181d6fa16' and \
			profile.wid == 'b5a9367e-680d-46c0-bb2c-73932a6d4007' and \
			profile.domain == 'example.com' and \
			profile.port == 2001, "set_dict() assignments did not match test data."


# def test_save_profiles():
# 	'''Tests userprofile.save_profiles()'''

# 	profile_test_folder = setup_test('save_profiles')
# 	profile1 = userprofile.Profile()
# 	profile1.name = 'Primary'
# 	profile1.id = '11111111-1111-1111-1111-111111111111'
# 	profile1.wid = '00000000-1111-2222-3333-444444444444'
# 	profile1.domain = 'example.com'
# 	profile1.isdefault = True

# 	profile2 = userprofile.Profile()
# 	profile2.name = 'Secondary'
# 	profile2.id = '22222222-2222-2222-2222-222222222222'
# 	profile2.wid = '00000000-1111-2222-3333-555555555555'
# 	profile2.domain = 'example.com'
# 	profile2.isdefault = False

# 	pman = userprofile.ProfileManager(profile_test_folder)
# 	status = pman.save_profiles()
# 	assert status.error(), "Failed to save profiles"

# def test_load_profiles():
# 	'''Tests userprofile.load_profiles()'''
	
# 	profile_test_folder = setup_test('load_profiles')
# 	profile1 = userprofile.Profile()
# 	profile1.name = 'Primary'
# 	profile1.id = '11111111-1111-1111-1111-111111111111'
# 	profile1.wid = '00000000-1111-2222-3333-444444444444'
# 	profile1.domain = 'example.com'
# 	profile1.isdefault = True

# 	profile2 = userprofile.Profile()
# 	profile2.name = 'Secondary'
# 	profile2.id = '22222222-2222-2222-2222-222222222222'
# 	profile2.wid = '00000000-1111-2222-3333-555555555555'
# 	profile2.domain = 'example.com'
# 	profile2.isdefault = False

# 	pman = userprofile.ProfileManager(profile_test_folder)
# 	status = pman.save_profiles()
# 	assert status.error(), "Failed to save profiles"
	
# 	status = pman.load_profiles()
# 	assert not status.error(), 'Failed to load profiles: %s' % status.info()

# 	profiles = pman.get_profiles()
# 	assert len(profiles) == 2, "load_profiles did not yield correct count"
# 	assert profiles[0].is_valid(), "Profile #1 not valid"
# 	assert profiles[0].name == 'Primary' and \
# 		profiles[0].id == '11111111-1111-1111-1111-111111111111' and \
# 		profiles[0].wid == '00000000-1111-2222-3333-444444444444' and \
# 		profiles[0].domain == 'example.com' and \
# 		profiles[0].isdefault, "Profile #1 didn't load correctly"
