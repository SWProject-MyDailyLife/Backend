from flask import Flask, request, jsonify, session, send_file
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from flask_cors import CORS
import os
import io
import gridfs
from flask_session import Session
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True, origins=["*"])

# Flask-Session 설정
# app.config['SESSION_TYPE'] = 'redis'
# app.config['SESSION_PERMANENT'] = False
# app.config['SESSION_USE_SIGNER'] = True
# app.config['SESSION_KEY_PREFIX'] = 'session:'
# app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379)

# # 세션 설정 초기화
# Session(app)

client = MongoClient('mongodb+srv://bsb1203:qxzdozhOGmOFUdLN@cluster0.cj1vuyu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['Photo_Diary']

users_collection = db['users']
photos_collection = db['photos']
messages_collection = db['messages']
fs = gridfs.GridFS(db)

access_type = 'args'

# Ensure the images directory exists
if not os.path.exists('images'):
    os.makedirs('images')

# 회원 가입
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data.get('user_id') or not data.get('password'):
        return jsonify({"message": "User ID and password are required"}), 400

    if users_collection.find_one({"user_id": data['user_id']}):
        return jsonify({"message": "User ID already exists"}), 400

    user = {
        "user_id": data['user_id'],
        "password": bcrypt.generate_password_hash(data['password']).decode('utf-8'),
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    users_collection.insert_one(user)
    return jsonify({"message": "Account created successfully"}), 201

# 로그인
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users_collection.find_one({"user_id": data['user_id']})
    if user and bcrypt.check_password_hash(user['password'], data['password']):
        session['user_id'] = user['user_id']
        print(f"User {user['user_id']} logged in, session: {session['user_id']}")  # 로그 출력
        return jsonify({"message": "Login successful", "user_id": user['user_id'], "sesson_id": session['user_id']}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# 로그아웃
@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logout successful"}), 200

# 사용자 목록 조회
@app.route('/api/users', methods=['GET'])
def get_users():
    users = list(users_collection.find({}, {"_id": 0, "user_id": 1}))
    return jsonify(users), 200

def signIn_as(arg):
    if(arg == 'args'):
        return request.args.get('user_id')
    
    if(arg == 'session'):
        return session.get('user_id')
    
    if(arg == 'header'):
        return request.headers.get('user_id')
    

# 사용자 사진 조회 (로그인 사용자만)
@app.route('/api/photos', methods=['GET'])
def get_photos():
    # user_id = request.args.get('user_id')
    # user_id = session.get('user_id')
    # print(session)
    # session_id = request.headers.get('Session-Id')
    # print(f"Session ID from request: {session_id}")
    # print(request.headers)
    # user_id = request.headers.get('user_id')
    user_id = signIn_as(access_type)
    print(f"user ID from request: {user_id}")
    # print(session)
    # user_id = session.get('user_id')
    
    # if 'user_id' not in session:
        # return jsonify({"message": "Unauthorized access"}), 401
    if not user_id:
        return jsonify({"message": "Unauthorized access"}), 401
    # if 'user_id' not in session:
    print('ok')
    
    photos = list(photos_collection.find({}, {"_id": 1, "keywords": 1, "user_id": 1, "file_id": 1}))
    result = []
    for photo in photos:
        photo_data = {
            "_id": str(photo["_id"]),
            "keywords": photo.get("keywords", []),
            "user_id": photo.get("user_id")
        }
        file_id = photo.get("file_id")
        if file_id:
            image_data = fs.get(file_id).read()
            photo_data["image"] = image_data.decode('latin1')  # 이미지 데이터를 인코딩하여 반환
        result.append(photo_data)

    return jsonify(result), 200

# 사진 업로드 (로그인 사용자만)
@app.route('/api/photos', methods=['POST'])
def upload_photo():
    # user_id = signIn_as(access_type)

    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"message": "Unauthorized access"}), 401

    image = data.get("image")
    keywords = data.get("keywords")

    if not image or not keywords:
        return jsonify({"message": "Image and keywords are required"}), 400

    image_data = base64.b64decode(image.split(",")[1])
    fs_id = fs.put(image_data, content_type="image/jpeg")

    photo = {
        "user_id": user_id,
        "keywords": keywords,
        "file_id": fs_id,
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    photo_id = photos_collection.insert_one(photo).inserted_id

    return jsonify({"message": "Photo uploaded successfully", "photo_id": str(photo_id)}), 201

# photo_id로 이미지 파일 제공
# @app.route('/api/photo/<photo_id>', methods=['GET'])
# def get_photo(photo_id):
#     if 'user_id' not in session:
#         return jsonify({"message": "Unauthorized access"}), 401
    
#     photo = photos_collection.find_one({"_id": ObjectId(photo_id)})
#     if not photo:
#         return jsonify({"message": "Photo not found"}), 404

#     file_id = photo['file_id']
#     image_data = fs.get(file_id)

#     return send_file(io.BytesIO(image_data.read()), mimetype=image_data.content_type, download_name=image_data.filename)

# 키워드로 사진 검색
@app.route('/api/photos/search', methods=['GET'])
def search_photos():
    # user_id = signIn_as(access_type)

    # if not user_id:
    #     return jsonify({"message": "Unauthorized access"}), 401
    
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"message": "Keyword is required"}), 400

    photos = list(photos_collection.find({"keywords": {"$regex": keyword, "$options": "i"}}, {"_id": 1, "keywords": 1, "user_id": 1, "file_id": 1}))
    
    results = []
    for photo in photos:
        photo_data = {
            "_id": str(photo["_id"]),
            "keywords": photo.get("keywords", []),
            "user_id": photo.get("user_id")
        }
        file_id = photo.get("file_id")
        if file_id:
            image_data = fs.get(file_id).read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            photo_data["photo_url"] = f"data:image/jpeg;base64,{base64_image}"
        results.append(photo_data)
    
    return jsonify(results), 200

# 사진 수정 (로그인 사용자만)
@app.route('/api/photos/<photo_id>', methods=['PUT'])
def update_photo(photo_id):

    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"message": "Unauthorized access"}), 401
    
    # if 'user_id' not in session:
    #     return jsonify({"message": "Unauthorized access"}), 401

    photo = photos_collection.find_one({"_id": ObjectId(photo_id), "user_id": user_id})
    
    if not photo:
        return jsonify({"message": "Photo not found or unauthorized"}), 404

    photos_collection.update_one(
        {"_id": ObjectId(photo_id)},
        {"$set": {"description": data['description'], "keywords": data['keywords'], "updated_at": datetime.datetime.now()}}
    )
    return jsonify({"message": "Photo updated successfully"}), 200

# 메시지 전송 (로그인 사용자만)
@app.route('/api/messages', methods=['POST'])
def send_message():

    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"message": "Unauthorized access"}), 401
    # if 'user_id' not in session:
    #     return jsonify({"message": "Unauthorized access"}), 401

    message = {
        "from_user_id": user_id,
        "to_user_id": data['to_user_id'],
        "message": data['message'],
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now(),
        "conversation": sorted([user_id, data['to_user_id']])
    }
    messages_collection.insert_one(message)
    return jsonify({"message": "Message sent successfully"}), 201

# 미리보기 메시지 조회 (로그인 사용자만)
@app.route('/api/messages', methods=['GET'])
def get_messages():
    user_id = signIn_as(access_type)

    if not user_id:
        return jsonify({"message": "Unauthorized access"}), 401
    
    pipeline = [
        {"$match": {"conversation": user_id}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": "$conversation",
            "message_id": {"$first": "$_id"},
            "conversation": {"$first": "$conversation"},
            "message": {"$first": "$message"},
        }},
        {"$project": {
            "_id": "$message_id",
            "message": 1,
            "to_user_id": {
                "$arrayElemAt": [
                    {"$filter": {
                        "input": "$conversation",
                        "as": "user",
                        "cond": {"$ne": ["$$user", user_id]}
                    }},
                    0
                ]
            }
        }}
    ]

    messages = list(messages_collection.aggregate(pipeline))

    # ObjectId를 문자열로 변환
    for message in messages:
        message['_id'] = str(message['_id'])

    return jsonify(messages), 200

# 특정 채팅방의 전체 메시지 조회 (로그인 사용자만)
@app.route('/api/messages/conversation', methods=['GET'])
def get_conversation_messages():
    user_id = signIn_as(access_type)

    if not user_id:
        return jsonify({"message": "Unauthorized access"}), 401

    # 쿼리 매개변수에서 other_user_id 가져오기
    other_user_id = request.args.get('other_user_id')
    if not other_user_id:
        return jsonify({"message": "other_user_id is required"}), 400

    conversation = [user_id, other_user_id]
    messages = list(messages_collection.find({"conversation": {"$all": conversation}}).sort("created_at", 1))
    
    for message in messages:
        message['_id'] = str(message['_id'])

    return jsonify(messages), 200

# # 모든 메시지 삭제 (테스트용)
# @app.route('/api/messages/delete_all', methods=['DELETE'])
# def delete_all_messages():
#     messages_collection.delete_many({})
#     return jsonify({"message": "All messages deleted successfully"}), 200

# 메시지 삭제 (로그인 사용자만)
@app.route('/api/messages/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    user_id = signIn_as(access_type)

    if not user_id:
        return jsonify({"message": "Unauthorized access"}), 401
    # if 'user_id' not in session:
    #     return jsonify({"message": "Unauthorized access"}), 401

    result = messages_collection.delete_one({"_id": ObjectId(message_id), "to_user_id": user_id})
    if result.deleted_count == 1:
        return jsonify({"message": "Message deleted successfully"}), 200
    else:
        return jsonify({"message": "Message not found or unauthorized"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port='5000')