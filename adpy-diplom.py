import requests
import json
import pprint
import time
import datetime

from pymongo import MongoClient
from collections import Counter

class Vkinder():
    TOKEN = 'b759f7c046868edeb57b6360e3b507fef5d425a1b34c681de0d378a9fadbc08db9c552f02f968b221ad91'
    VERSION = '5.95'
    RESULT_DB = MongoClient().result_db

    def __init__(self, main_user_id):
        self.main_user_id = main_user_id

    def find_main_user_info(self, main_user_id):
        response_main_user = requests.get('https://api.vk.com/method/users.get', {
            'access_token': self.TOKEN,
            'user_ids': main_user_id,
            'fields': 'bdate, sex, interests, city',
            'v': self.VERSION
        })
        return response_main_user.json()['response'][0]

    def find_users(self, main_user_info):
        sex_for_find = 0
        if main_user_info['sex'] == 1:
            sex_for_find = 2
        elif main_user_info['sex'] == 2:
            sex_for_find = 1

        min_age = 18
        max_age = 50
        if 'bdate' in main_user_info:
            age_for_find = datetime.date.today().year - int(main_user_info['bdate'].split('.')[2])
            min_age = age_for_find - 2
            max_age = age_for_find + 2

        params_for_find = {
            'access_token': self.TOKEN,
            'sex': sex_for_find,
            'age_from': min_age,
            'age_to': max_age,
            'has_photo': 1,
            'fields': 'interests',
            'count': 1000,
            'city': main_user_info['city']['id'],
            'v': self.VERSION
        }

        response_find_users = requests.get('https://api.vk.com/method/users.search', params_for_find)
        return response_find_users.json()['response']['items']

    def sort_users(self, finded_users, main_user_info):
        for user in finded_users:
            if user['is_closed']:
                finded_users.remove(user)

        if main_user_info['interests'] != '':
            splitted_main_user_interests = main_user_info['interests'].split(' ')
            for user in finded_users:
                counter = 0
                if 'interests' in user:
                    splitted_interests = user['interests'].split(' ')
                    word_counter = Counter(splitted_interests)
                    for interest in splitted_main_user_interests:
                        counter += word_counter[interest]
                user['weight'] = counter

            finded_users.sort(key=lambda dict: dict['weight'], reverse=True)

        old_users = self.RESULT_DB.result.find({'main_user_id': self.main_user_id})
        for old_user in old_users:
            for user in finded_users:
                if user['id'] == old_user['finded_user']:
                    finded_users.remove(user)
        return finded_users[0:10]

    def find_and_sort_photos(self, finded_users):
        unsorted_photos = []
        for user in finded_users:
            params = {
                'access_token': self.TOKEN,
                'owner_id': user['id'],
                'extended': 1,
                'album_id': 'profile',
                'v': self.VERSION
            }
            response_get_photos = requests.get('https://api.vk.com/method/photos.get', params)
            unsorted_photos.append({
                'id': user['id'],
                'photos': response_get_photos.json()['response']['items']
            })
            time.sleep(0.4)
            print('.')

        sorted_users = []
        for user in unsorted_photos:
            unsorted_ids_of_photos = []
            for photo in user['photos']:
                unsorted_ids_of_photos.append({
                    'id': photo['id'],
                    'likes': photo['likes']['count']
                })
            unsorted_ids_of_photos.sort(key=lambda dict: dict['likes'], reverse=True)
            unsorted_ids_of_photos = unsorted_ids_of_photos[0:3]
            sorted_users.append({
                'id': user['id'],
                'photos': unsorted_ids_of_photos
            })
        return sorted_users

    def write_to_json_and_db(self, file):
        with open('result.json', 'w', encoding='utf8') as json_file:
            json.dump(file, json_file, ensure_ascii=False)

        data = []
        for user in file:
            data.append({
                'main_user_id': self.main_user_id,
                'finded_user': user['id']
            })
        self.RESULT_DB.result.insert_many(data)

    def start(self):
        main_user_info = self.find_main_user_info(self.main_user_id)
        finded_users = self.find_users(main_user_info)
        sorted_users = self.sort_users(finded_users, main_user_info)
        final_users = self.find_and_sort_photos(sorted_users)
        self.write_to_json_and_db(final_users)
        pprint.pprint(final_users)

if __name__ == '__main__':
    vkinder = Vkinder('9')
    vkinder.start()