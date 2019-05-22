import requests
import json
import pprint
import time
import datetime

from pymongo import MongoClient
from collections import Counter

class User():
    def __init__(self, id, first_name, last_name, is_closed, sex, info, weight = 0):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.is_closed = is_closed
        self.sex = sex
        self.info = info
        self.weight = weight

class Vkinder():
    TOKEN = 'b759f7c046868edeb57b6360e3b507fef5d425a1b34c681de0d378a9fadbc08db9c552f02f968b221ad91'
    VERSION = '5.95'

    def __init__(self, main_user_id, database):
        response_main_user = requests.get('https://api.vk.com/method/users.get', {
            'access_token': self.TOKEN,
            'user_ids': main_user_id,
            'fields': 'bdate, sex, interests, music, books, city',
            'v': self.VERSION
        })

        self.RESULT_DB = database
        main_user_info = response_main_user.json()['response'][0]
        self.main_user = User(
            main_user_info.pop('id'),
            main_user_info.pop('first_name'),
            main_user_info.pop('last_name'),
            main_user_info.pop('is_closed'),
            main_user_info.pop('sex'),
            main_user_info
        )

    def find_users(self):
        sex_for_find = 0
        if self.main_user.sex == 1:
            sex_for_find = 2
        elif self.main_user.sex == 2:
            sex_for_find = 1

        min_age = 18
        max_age = 50
        if 'bdate' in self.main_user.info:
            age_for_find = datetime.date.today().year - int(self.main_user.info['bdate'].split('.')[2])
            min_age = age_for_find - 2
            max_age = age_for_find + 2

        params_for_find = {
            'access_token': self.TOKEN,
            'sex': sex_for_find,
            'age_from': min_age,
            'age_to': max_age,
            'has_photo': 1,
            'fields': 'interests, music, books, sex, city',
            'count': 1000,
            'city': self.main_user.info['city']['id'],
            'v': self.VERSION
        }

        response_find_users = requests.get('https://api.vk.com/method/users.search', params_for_find)
        users = []
        for user in response_find_users.json()['response']['items']:
            users.append(User(
                user.pop('id'),
                user.pop('first_name'),
                user.pop('last_name'),
                user.pop('is_closed'),
                user.pop('sex'),
                user
            ))
        return users

    def sort_users(self, finded_users):
        if self.main_user.info['interests'] != '':
            splitted_main_user_interests = self.main_user.info['interests'].split(' ')
            for user in finded_users:
                counter = 0
                if 'interests' in user.info:
                    splitted_interests = user.info['interests'].split(' ')
                    word_counter = Counter(splitted_interests)
                    for interest in splitted_main_user_interests:
                        counter += word_counter[interest]
                user.weight += counter * 3

        if self.main_user.info['music'] != '':
            splitted_main_user_interests = self.main_user.info['music'].split(' ')
            for user in finded_users:
                counter = 0
                if 'music' in user.info:
                    splitted_interests = user.info['music'].split(' ')
                    word_counter = Counter(splitted_interests)
                    for interest in splitted_main_user_interests:
                        counter += word_counter[interest]
                user.weight += counter * 2

        if self.main_user.info['books'] != '':
            splitted_main_user_interests = self.main_user.info['books'].split(' ')
            for user in finded_users:
                counter = 0
                if 'books' in user.info:
                    splitted_interests = user.info['books'].split(' ')
                    word_counter = Counter(splitted_interests)
                    for interest in splitted_main_user_interests:
                        counter += word_counter[interest]
                user.weight += counter

            finded_users.sort(key=lambda dict: dict.weight, reverse=True)

        old_users = self.RESULT_DB.result.find({'main_user_id': self.main_user.id})
        try:
            old_users[0]
            for old_user in old_users[0]['finded_users']:
                for user in finded_users:
                    if user.id == old_user or user.is_closed:
                        finded_users.remove(user)
        except IndexError:
            for user in finded_users:
                if user.is_closed:
                    finded_users.remove(user)

        return finded_users[0:10]

    def find_and_sort_photos(self, finded_users):
        unsorted_photos = []
        for user in finded_users:
            params = {
                'access_token': self.TOKEN,
                'owner_id': user.id,
                'extended': 1,
                'album_id': 'profile',
                'v': self.VERSION
            }
            response_get_photos = requests.get('https://api.vk.com/method/photos.get', params)
            unsorted_photos.append({
                'id': user.id,
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

    def write_to_db(self, file):
        old_db = self.RESULT_DB.result.find({'main_user_id': self.main_user.id})

        try:
            old_db[0]
            data = []
            for user in file:
                data.append(user['id'])
            self.RESULT_DB.result.update_many({'main_user_id': self.main_user.id}, {'$push': {'finded_users': {'$each': data}}})
        except IndexError:
            data = {
                'main_user_id': self.main_user.id,
                'finded_users': []
            }
            for user in file:
                data['finded_users'].append(user['id'])
            self.RESULT_DB.result.insert_one(data)

    def start(self):
        finded_users = self.find_users()
        sorted_users = self.sort_users(finded_users)
        final_users = self.find_and_sort_photos(sorted_users)
        self.write_to_db(final_users)
        pprint.pprint(final_users)

if __name__ == '__main__':
    vkinder = Vkinder('9', MongoClient().result_db)
    vkinder.start()