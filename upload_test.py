import requests

# 세션 생성
session = requests.Session()

# 로그인
login_url = 'http://127.0.0.1:5000/api/login'
login_data = {
    "user_id": "김민수",
    "password": "test"
}
login_response = session.post(login_url, json=login_data)
print("Login Response:", login_response.json())

# # 이미지 업로드 함수
# def upload_image(file_path, description, keywords):
#     upload_url = 'http://127.0.0.1:5000/api/photos'
#     with open(file_path, 'rb') as f:
#         files = {'image': f}
#         data = {'description': description, 'keyword': keywords}
#         upload_response = session.post(upload_url, files=files, data=data)
#         try:
#             upload_response_json = upload_response.json()
#             print("Upload Response:", upload_response_json)
#         except ValueError:
#             print("Upload Response: Not a JSON response")
#             print(upload_response.text)

# # 업로드할 이미지 파일과 관련 정보
# images_info = [
#     # {'file': 'red_panda.png', 'description': 'Red panda in a tree', 'keywords': 'red panda, tree, cute'},
#     # {'file': 'Quokka.jpg', 'description': 'Quokka smiling', 'keywords': 'quokka, smile, animal'},
#     # {'file': 'sunset.jpeg', 'description': 'Beautiful tropical sunset', 'keywords': 'tropical, sunset, beach'},
#     # {'file': 'Star_trails.jpg', 'description': 'Star trails over trees', 'keywords': 'star trails, night, sky'},
#     {'file': 'Stargazing.jpeg', 'description': 'Stargazing at night', 'keywords': 'stargazing, night, stars'}
# ]

# # 이미지 업로드
# for info in images_info:
#     upload_image(info['file'], info['description'], info['keywords'])

# 이미지 수정 함수
# def update_image(photo_id, new_description, new_keywords):
#     update_url = f'http://127.0.0.1:5000/api/photos/{photo_id}'
#     data = {
#         'description': new_description,
#         'keywords': new_keywords
#     }
#     update_response = session.put(update_url, json=data)
#     try:
#         update_response_json = update_response.json()
#         print("Update Response:", update_response_json)
#     except ValueError:
#         print("Update Response: Not a JSON response")
#         print(update_response.text)

# update_image("666565f6deb5d19e3d16cc83", "Update Red panda in a tree", "red panda, tree, cute, update")

# 사진 조회
search_photos = 'http://127.0.0.1:5000/api/photos'
response = session.get(search_photos)
try:
    print("Photos Response:", response.json())
except ValueError:
    print("Photos Response: Not a JSON response")

# 키워드로 사진 검색
search_url = 'http://127.0.0.1:5000/api/photos/search'
params = {'keyword': 'update'}
search_response = session.get(search_url, params=params)
try:
    print("Search Photos Response:", search_response.json())
except ValueError:
    print("Search Photos Response: Not a JSON response")

# 로그아웃
logout_url = 'http://127.0.0.1:5000/api/logout'
logout_response = session.post(logout_url)
try:
    print("Logout Response:", logout_response.json())
except ValueError:
    print("Logout Response: Not a JSON response")
