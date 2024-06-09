from flask import Flask, request, jsonify, session, send_from_directory, send_file
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from flask_cors import CORS
import os
import io
import gridfs

app = Flask(__name__)
app.secret_key = 'your_secret_key'
bcrypt = Bcrypt(app)
CORS(app)

client = MongoClient('mongodb+srv://bsb1203:qxzdozhOGmOFUdLN@cluster0.cj1vuyu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['Photo_Diary']

users_collection = db['users']
photos_collection = db['photos']
messages_collection = db['messages']
fs = gridfs.GridFS(db)

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
        return jsonify({"message": "Login successful"}), 200
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

# 사용자 사진 조회 (로그인 사용자만)
@app.route('/api/photos', methods=['GET'])
def get_photos():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized access"}), 401
    
    photos = list(photos_collection.find({}, {"_id": 1, "photo_url": 1, "description": 1, "keywords": 1, "user_id": 1}))
    # ObjectId를 문자열로 변환
    for photo in photos:
        photo['_id'] = str(photo['_id'])
    return jsonify(photos), 200

# 사진 업로드 (로그인 사용자만)
@app.route('/api/photos', methods=['POST'])
def upload_photo():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized access"}), 401

    description = request.form["description"]
    keyword = request.form["keyword"]
    image = request.files["image"]

    # 이미지 파일을 GridFS에 저장
    fs_id = fs.put(image, filename=image.filename, content_type=image.content_type)

    # DB에 저장
    photo = {
        "user_id": session['user_id'],
        "description": description,
        "keywords": keyword,
        "file_id": fs_id,
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    photo_id = photos_collection.insert_one(photo).inserted_id

    return jsonify({"message": "Photo uploaded successfully", "photo_id": str(photo_id)}), 201

# photo_id로 이미지 파일 제공
@app.route('/api/photo/<photo_id>', methods=['GET'])
def get_photo(photo_id):
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized access"}), 401
    
    photo = photos_collection.find_one({"_id": ObjectId(photo_id)})
    if not photo:
        return jsonify({"message": "Photo not found"}), 404

    file_id = photo['file_id']
    image_data = fs.get(file_id)

    return send_file(io.BytesIO(image_data.read()), mimetype=image_data.content_type, download_name=image_data.filename)

# 키워드로 사진 검색
@app.route('/api/photos/search', methods=['GET'])
def search_photos():
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({"message": "Keyword is required"}), 400

    photos = list(photos_collection.find({"keywords": {"$regex": keyword, "$options": "i"}}, {"_id": 1, "description": 1, "keywords": 1, "user_id": 1}))
    
    results = []
    for photo in photos:
        photo_id = photo['_id']
        results.append({
            "_id": str(photo_id),
            "description": photo['description'],
            "keywords": photo['keywords'],
            "user_id": photo['user_id']
        })
    return jsonify(results), 200

# 사진 수정 (로그인 사용자만)
@app.route('/api/photos/<photo_id>', methods=['PUT'])
def update_photo(photo_id):
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized access"}), 401

    data = request.get_json()
    photo = photos_collection.find_one({"_id": ObjectId(photo_id), "user_id": session['user_id']})
    
    if not photo:
        return jsonify({"message": "Photo not found or unauthorized"}), 404

    photos_collection.update_one(
        {"_id": ObjectId(photo_id)},
        {"$set": {"description": data['description'], "keywords": data['keywords'], "updated_at": datetime.datetime.now()}}
    )
    return jsonify({"message": "Photo updated successfully"}), 200

# # 업로드된 모든 사진 삭제 (테스트용)
# @app.route('/api/photos/delete_all', methods=['DELETE'])
# def delete_all_photos():
#     if 'user_id' not in session:
#         return jsonify({"message": "Unauthorized access"}), 401

#     # DB에서 모든 사진 삭제
#     photos = photos_collection.find({})
#     for photo in photos:
#         if 'file_id' in photo:
#             fs.delete(photo['file_id'])
#     photos_collection.delete_many({})
    
#     return jsonify({"message": "All photos deleted successfully"}), 200

# 메시지 전송 (로그인 사용자만)
@app.route('/api/messages', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized access"}), 401

    data = request.get_json()
    message = {
        "from_user_id": session['user_id'],
        "to_user_id": data['to_user_id'],
        "photo_id": data['photo_id'],
        "message": data['message'],
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    messages_collection.insert_one(message)
    return jsonify({"message": "Message sent successfully"}), 201

# 받은 메시지 조회 (로그인 사용자만)
@app.route('/api/messages', methods=['GET'])
def get_messages():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized access"}), 401

    messages = list(messages_collection.find({"to_user_id": session['user_id']}, {"_id": 1, "from_user_id": 1, "photo_id": 1, "message": 1, "created_at": 1}))
    # ObjectId를 문자열로 변환
    for message in messages:
        message['_id'] = str(message['_id'])
        message['photo_id'] = str(message['photo_id'])
    return jsonify(messages), 200

# 메시지 삭제 (로그인 사용자만)
@app.route('/api/messages/<message_id>', methods=['DELETE'])
def delete_message(message_id):
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized access"}), 401

    result = messages_collection.delete_one({"_id": ObjectId(message_id), "to_user_id": session['user_id']})
    if result.deleted_count == 1:
        return jsonify({"message": "Message deleted successfully"}), 200
    else:
        return jsonify({"message": "Message not found or unauthorized"}), 404

# 메시지 답장 (로그인 사용자만)
@app.route('/api/messages/<message_id>', methods=['POST'])
def reply_message(message_id):
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized access"}), 401

    original_message = messages_collection.find_one({"_id": ObjectId(message_id), "to_user_id": session['user_id']})
    if not original_message:
        return jsonify({"message": "Message not found or unauthorized"}), 404

    data = request.get_json()
    reply = {
        "from_user_id": session['user_id'],
        "to_user_id": original_message['from_user_id'],
        "photo_id": original_message['photo_id'],
        "message": data['message'],
        "created_at": datetime.datetime.now(),
        "updated_at": datetime.datetime.now()
    }
    messages_collection.insert_one(reply)
    return jsonify({"message": "Reply sent successfully"}), 201

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
