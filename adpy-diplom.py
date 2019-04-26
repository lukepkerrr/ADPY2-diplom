import requests
import json
import pprint
import time

TOKEN = 'b759f7c046868edeb57b6360e3b507fef5d425a1b34c681de0d378a9fadbc08db9c552f02f968b221ad91'
VERSION = '5.95'

def find_main_user_info(main_user_id):
    response_main_user = requests.get('https://api.vk.com/method/users.get', {
        'access_token': TOKEN,
        'user_ids': main_user_id,
        'fields': 'bdate, sex, interests, city',
        'v': VERSION
    })
    return response_main_user.json()['response'][0]

def find_users(main_user_info):
    sex_for_find = 0
    if main_user_info['sex'] == 1:
        sex_for_find = 2
    elif main_user_info['sex'] == 2:
        sex_for_find = 1

    params_for_find = {
        'access_token': TOKEN,
        'sex': sex_for_find,
        'count': 10,
        # 'interests': main_user_info['interests'],
        'has_photo': 1,
        'city': main_user_info['city']['id'],
        'v': VERSION
    }

    response_find_users = requests.get('https://api.vk.com/method/users.search', params_for_find)
    return response_find_users.json()['response']['items']

def find_and_sort_photos(finded_users):
    unsorted_photos = []
    for user in finded_users:
        params = {
            'access_token': TOKEN,
            'owner_id': user['id'],
            'extended': 1,
            'album_id': 'profile',
            'v': VERSION
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

def write_to_json(file):
    with open('result.json', 'w', encoding='utf8') as json_file:
        json.dump(file, json_file, ensure_ascii=False)

if __name__ == '__main__':
    main_user_info = find_main_user_info('igorvasile')
    finded_users = find_users(main_user_info)
    sorted_users = find_and_sort_photos(finded_users)
    write_to_json(sorted_users)
    pprint.pprint(sorted_users)