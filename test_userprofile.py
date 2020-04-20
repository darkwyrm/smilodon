import os

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


def test_save_profiles():
	'''Tests userprofile.save_profiles()'''

	profile_test_folder = setup_test('save_profiles')
	profile1 = userprofile.Profile()
	profile1.name = 'Primary'
	profile1.id = '11111111-1111-1111-1111-111111111111'
	profile1.wid = '00000000-1111-2222-3333-444444444444'
	profile1.domain = 'example.com'
	profile1.isdefault = True

	profile2 = userprofile.Profile()
	profile2.name = 'Secondary'
	profile2.id = '22222222-2222-2222-2222-222222222222'
	profile2.wid = '00000000-1111-2222-3333-555555555555'
	profile2.domain = 'example.com'
	profile2.isdefault = False

	assert userprofile.save_profiles(profile_test_folder, [profile1, profile2]), \
		"Failed to save profiles"

def test_load_profiles():
	'''Tests userprofile.load_profiles()'''
	
	profile_test_folder = setup_test('load_profiles')
	profile1 = userprofile.Profile()
	profile1.name = 'Primary'
	profile1.id = '11111111-1111-1111-1111-111111111111'
	profile1.wid = '00000000-1111-2222-3333-444444444444'
	profile1.domain = 'example.com'
	profile1.isdefault = True

	profile2 = userprofile.Profile()
	profile2.name = 'Secondary'
	profile2.id = '22222222-2222-2222-2222-222222222222'
	profile2.wid = '00000000-1111-2222-3333-555555555555'
	profile2.domain = 'example.com'
	profile2.isdefault = False

	assert userprofile.save_profiles(profile_test_folder, [profile1, profile2]), \
		"Failed to save profiles"
	
	status = userprofile.load_profiles(os.path.join(profile_test_folder, 'profiles.json'))
	assert not status['error'], 'Failed to load profiles: %s' % status['error']

	profiles = status['profiles']
	assert len(profiles) == 2, "load_profiles did not yield correct count"
	assert profiles[0].is_valid(), "Profile #1 not valid"
	assert profiles[0].name == 'Primary' and \
		profiles[0].id == '11111111-1111-1111-1111-111111111111' and \
		profiles[0].wid == '00000000-1111-2222-3333-444444444444' and \
		profiles[0].domain == 'example.com' and \
		profiles[0].isdefault, "Profile #1 didn't load correctly"
