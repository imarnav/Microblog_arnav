import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or "mysql+pymysql://root:r6kd1lfa@localhost:3306/ankit"
	# 'sqlite:///' + os.path.join(basedir,'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	POSTS_PER_PAGE = 10
	MAIL_SERVER="smtp.googlemail.com"
	MAIL_PORT=587
	MAIL_USE_TLS=1
	MAIL_USERNAME="18001003021@jcboseust.ac.in"
	MAIL_PASSWORD="Legends@786"
	ADMINS=["18001003021@jcboseust.ac.in"]