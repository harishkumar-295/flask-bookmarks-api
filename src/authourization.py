from flask import Blueprint, app, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
import validators
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt_identity,get_jwt,get_jwt_header,decode_token, verify_jwt_in_request
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_409_CONFLICT
from .database import User,db
from flasgger import swag_from

auth = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

@auth.post('/register')
@swag_from('./docs/auth/registration.yaml')
def register():
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']
    
    if len(password) < 6:
        return jsonify({"msg": "Password is too short!!!"}),HTTP_400_BAD_REQUEST
    
    if len(username) < 3:
        return jsonify({"msg": "Username is too short!!!"}),HTTP_400_BAD_REQUEST
    
    if not username.isalnum() or " " in username:
        return jsonify({"msg": "Username should not have a space and should be alphanumeric"}),HTTP_400_BAD_REQUEST
    
    if not validators.email(email):
        return jsonify({"msg": "Email is not valid"}),HTTP_400_BAD_REQUEST
    
    if User.query.filter_by(email=email).first() is not None:
        return jsonify({"msg": "Email already exists..!"}),HTTP_409_CONFLICT
    
    if User.query.filter_by(username=username).first() is not None:
        return jsonify({"msg": "Username already exists..!"}),HTTP_409_CONFLICT
    
    pwd_hash = generate_password_hash(password)
    
    user = User(username=username, password=pwd_hash, email=email)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"msg":"user created successfully",
                    "user":{
                                "username": username,
                                "email": email
                            }
                    }
                   ),HTTP_201_CREATED
    
@auth.post("/login")
@swag_from('./docs/auth/login.yaml')
def login():
    email = request.json.get('email',"")
    password = request.json.get('password',"")
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        is_pass_correct = check_password_hash(user.password,password)
        
        if is_pass_correct:
            access_token = create_access_token(identity=user.id,)
            refresh_token = create_refresh_token(identity=user.id)
            
            return jsonify({'user':{
                                    "refresh_token":refresh_token,
                                    "access_token":access_token,
                                    "username":user.username,
                                    "email":user.email
                                    }
                            }
                           ),HTTP_200_OK
    return jsonify({'msg': 'Wrong credentials'}), HTTP_401_UNAUTHORIZED

@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return jsonify({
        'username': user.username,
        'email': user.email
    }), HTTP_200_OK
    

@auth.get('/token/refresh')
@jwt_required(refresh=True)
def refresh_users_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({
        'access': access
    }), HTTP_200_OK


# get token and verify if it's secret key    
@auth.get('/verifyToken')
def check_if_token_is_valid():
    token = request.headers.get('Token')
    if not token:
        return jsonify({"success": False}),HTTP_401_UNAUTHORIZED
    decode_token(token)
    return jsonify({"success": True})
    
    
   
    