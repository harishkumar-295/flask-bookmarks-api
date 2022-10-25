from flask import Blueprint, app, request, jsonify
import validators
from .database import BookMark,db
from src.constants.http_status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT
from flask_jwt_extended import get_jwt_identity,jwt_required
from flasgger import swag_from

bookmark = Blueprint("bookmark", __name__, url_prefix="/api/v1/bookmarks")

@bookmark.route('/',methods=['GET', 'POST'])
@jwt_required()
def handle_bookmarks():
    current_user = get_jwt_identity()
    if request.method == 'POST':
        body = request.get_json().get('body','')
        url = request.get_json().get('url','')
        
        if not validators.url(url):
            return jsonify({"msg": "Invalid url"}),HTTP_400_BAD_REQUEST
        
        if BookMark.query.filter_by(url=url).first():
            return jsonify({"msg": "Url already exists"}),HTTP_409_CONFLICT
        
        bookmark = BookMark(url=url,body=body,user_id = current_user)
        db.session().add(bookmark)
        db.session().commit()
        
        return jsonify({
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visits":bookmark.visits,
            "body": bookmark.body,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at
        }),HTTP_201_CREATED
    else:
        
        page = request.args.get('page',1,type=int)
        per_page = request.args.get('per_page',5,type = int)
        
        bookmarks = BookMark.query.filter_by(user_id = current_user).paginate(page=page, per_page=per_page)
        
        data = [{
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visits": bookmark.visits,
            "body": bookmark.body,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at} for bookmark in bookmarks.items]
        
        meta = {
            "page": bookmarks.page,
            'pages': bookmarks.pages,
            'total_count': bookmarks.total,
            'prev_page': bookmarks.prev_num,
            'next_page': bookmarks.next_num,
            'has_next': bookmarks.has_next,
            'has_prev': bookmarks.has_prev,
        }
        
        return jsonify({"data": data,"meta":meta}),HTTP_200_OK
    
@bookmark.get('/<int:id>')
@jwt_required()
def get_bookmark(id):
    current_user = get_jwt_identity()
    
    bookmark = BookMark.query.filter_by(user_id = current_user,id=id).first()
    
    if not bookmark:
        return jsonify({'msg': "Bookmark not found"}),HTTP_404_NOT_FOUND
    
    return jsonify({
            "id": bookmark.id,
            "url": bookmark.url,
            "short_url": bookmark.short_url,
            "visits": bookmark.visits,
            "body": bookmark.body,
            "created_at": bookmark.created_at,
            "updated_at": bookmark.updated_at}),HTTP_200_OK
    
@bookmark.delete("/<int:id>")
@jwt_required()
def delete_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = BookMark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()

    return jsonify({}), HTTP_204_NO_CONTENT
    

@bookmark.put('/<int:id>')
@bookmark.patch('/<int:id>')
@jwt_required()
def editbookmark(id):
    current_user = get_jwt_identity()

    bookmark = BookMark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({'message': 'Item not found'}), HTTP_404_NOT_FOUND

    body = request.get_json().get('body', '')
    url = request.get_json().get('url', '')

    if not validators.url(url):
        return jsonify({
            'error': 'Enter a valid url'
        }), HTTP_400_BAD_REQUEST

    bookmark.url = url
    bookmark.body = body

    db.session.commit()

    return jsonify({
        'id': bookmark.id,
        'url': bookmark.url,
        'short_url': bookmark.short_url,
        'visit': bookmark.visits,
        'body': bookmark.body,
        'created_at': bookmark.created_at,
        'updated_at': bookmark.updated_at,
    }), HTTP_200_OK
    

@bookmark.get("/stats")
@jwt_required()
@swag_from("./docs/bookmarks/stats.yaml")
def get_stats():
    current_user = get_jwt_identity()

    items = BookMark.query.filter_by(user_id=current_user).all()
    
    data = [{
        'visits': item.visits,
        'url': item.url,
        'id': item.id,
        'short_url': item.short_url,
    } for item in items]


    return jsonify({'data': data}), HTTP_200_OK