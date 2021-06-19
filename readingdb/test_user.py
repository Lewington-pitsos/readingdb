from readingdb.user import User
import unittest

class TestDB(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_user_from_adjacency_patten_data(self):
        user_data = [
            {
                'PK': 'User#12923-nd12u-123n-12812-12213',
                'SK': 'User#12923-nd12u-123n-12812-12213'
            },
            {
                'PK': 'User#12923-nd12u-123n-12812-12213',
                'SK': 'AccessGroup#23123123'
            },
            {
                'PK': 'User#12923-nd12u-123n-12812-12213',
                'SK': 'AccessGroup#717811j176'
            },
            {
                'PK': 'User#12923-nd12u-123n-12812-12213',
                'SK': 'Org#28122123',
                'OrgName': 'AEC'
            }
        ]

        usr = User.from_raw(user_data)

        output = {
            'Sub': '12923-nd12u-123n-12812-12213',
            'AccessGroups': ['23123123', '717811j176'],
            'Org': {
                'OrgName': 'AEC',
                'OrgID': '28122123'
            }
        }

        self.assertDictEqual(output, usr.json())
    
    def test_user_raises_errors_on_bad_data(self):
        user_data = [
            {
                'PK': 'User#12923-nd12u-123n-12812-12213',
                'SK': 'User#12923-nd12u-123n-12812-12213'
            },
            {
                'PK': 'User#12923-nd12u-123n-12812-12213',
                'SK': 'User#12923-nd12u-123n-12812-12213'
            },
        ]

        self.assertRaises(ValueError, User.from_raw, user_data)

    def test_user_data_extract(self):
        user_data = {
            'Sub': '12923-nd12u-123n-12812-12213',
            'AccessGroups': ['23123123', '717811j176'],
            'Org': {
                'Name': 'AEC',
                'ID': '28122123'
            }
        }
        usr = User(user_data)
        j = usr.json()

        self.assertEqual(user_data, j)
