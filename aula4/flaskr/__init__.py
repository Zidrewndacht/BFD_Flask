# flaskr/__init__.py
import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    
    os.makedirs(app.instance_path, exist_ok=True)

    # Registra o blueprint auth
    from . import auth
    app.register_blueprint(auth.bp)

    # Registra o blueprint blog
    from . import blog
    app.register_blueprint(blog.bp)

    #novo (Aula4)
    #note que DB não é uma blueprint!
    from . import db
    db.init_app(app)

    # Define a rota raiz '/' como um alias para blog.index
    # Isso permite que http://127.0.0.1:5000/ funcione
    app.add_url_rule('/', endpoint='index')

    return app