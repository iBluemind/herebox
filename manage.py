from hereboxweb import manager
from hereboxweb.utils import initialize_db, compress, upload_to_s3, build_compressed_assets


@manager.command
def initial():
    initialize_db()


@manager.command
def build():
    build_compressed_assets()


@manager.command
def upload():
    upload_to_s3()


@manager.command
def run():
    from hereboxweb import app
    from config import DEBUG, PORT
    compress()
    app.run(host='0.0.0.0', debug=DEBUG, port=PORT)


if __name__ == "__main__":
    manager.run()