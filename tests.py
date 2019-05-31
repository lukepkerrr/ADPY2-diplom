import unittest

from ADPYD.diplom import *

class Test(unittest.TestCase):
    def test_is_instance_of_vkinder(self):
        self.assertIsInstance(vkinder, Vkinder)

    def test_find_users(self):
        self.assertIsInstance(vkinder.find_users(), list)

    def test_find_users_is_instance_of_user(self):
        self.assertIsInstance(vkinder.find_users()[0], User)

    def test_count_weight(self):
        self.assertNotEqual(vkinder.find_users(), vkinder.count_weight(vkinder.find_users()))

    def test_sort_users(self):
        for_sort = vkinder.find_users()
        self.assertEqual(len(vkinder.sort_users(for_sort)), 10)

    def test_sort_users_is_instance_of_user(self):
        for_sort = vkinder.find_users()
        self.assertIsInstance(vkinder.sort_users(for_sort)[0], User)

    def test_find_and_sort_photos(self):
        for_photos = vkinder.sort_users(vkinder.find_users())
        self.assertEqual(len(vkinder.find_and_sort_photos(for_photos)), 10)

    def test_find_and_sort_photosv_is_list(self):
        for_photos = vkinder.sort_users(vkinder.find_users())
        self.assertIsInstance(vkinder.find_and_sort_photos(for_photos), list)

if __name__ == '__main__':
    vkinder = Vkinder('9', MongoClient().result_db)

    unittest.main()