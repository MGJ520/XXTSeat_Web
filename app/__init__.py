# app/__init__.py
from flask import Flask, send_from_directory

import os



def create_app():
    app = Flask(__name__)

    # app.config.from_object('config.DevelopmentConfig')  # 加载配置


    # 注册蓝本
    # from app.errors import errors as errors_blueprint
    # app.register_blueprint(errors_blueprint)

    # 自定义静态文件路径
    @app.route('/<path:filename>')
    def custom_static(filename):
        return send_from_directory(os.path.join(app.root_path, 'static'), filename)

    from app.user import user as user_blueprint
    app.register_blueprint(user_blueprint)

    from app.index import index as index_blueprint
    app.register_blueprint(index_blueprint)


    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint)


    return app