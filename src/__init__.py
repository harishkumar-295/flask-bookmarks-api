from datetime import timedelta
from flask import Flask,redirect,jsonify
import os
from src.constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from src.database import db
from os import path
from flask_jwt_extended import JWTManager
from flasgger import Swagger,swag_from
from src.config.swagger import template,swagger_config


DB_NAME = "bookmarks.db"

def create_app(test_config=None):
    app = Flask(__name__,instance_relative_config=True)
    
    
    
    if test_config is None:
        # app.config.from_mapping(SECRET_KEY = os.getenv('SECRET_KEY'))
        app.config['SCRET_KEY'] = os.getenv('SECRET_KEY')
        
        # app.config.from_mapping(SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI'))
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_NAME}"
        app.config['FLASK_ENV'] = os.getenv('FLASK_ENV')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
        
        SWAGGER={
                'title': "Bookmarks API",
                'uiversion': 3
            }
    else:
        app.config.from_mapping(test_config)
        
    db.app = app
    db.init_app(app)
    
    JWTManager(app)
    
    from .database import User,BookMark
    create_database(app)
    
    from .authourization import auth
    from .bookmarks import bookmark
    app.register_blueprint(auth)
    app.register_blueprint(bookmark)
    
    Swagger(app, config=swagger_config, template=template)

    
    @app.get('/<short_url>')
    @swag_from('./docs/short_url.yaml')
    def redirect_to_url(short_url):
        bookmark = BookMark.query.filter_by(short_url=short_url).first_or_404()

        if bookmark:
            bookmark.visits = bookmark.visits+1
            db.session.commit()
            return redirect(bookmark.url)
    
    @app.errorhandler(HTTP_404_NOT_FOUND)
    def handle_404(e):
        return jsonify({'error': 'Not found'}), HTTP_404_NOT_FOUND

    @app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
    def handle_500(e):
        return jsonify({'error': 'Something went wrong, we are working on it'}), HTTP_500_INTERNAL_SERVER_ERROR
    
    return app

def create_database(app):
    if not path.exists('src/' + DB_NAME):
        with app.app_context():
            db.create_all()
            print("db created successfully") 