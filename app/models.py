from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
from datetime import datetime
from app import db
from flask_login import UserMixin
from app import login
from time import time
import jwt
from app import app



followers = db.Table('followers',
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	posts = db.relationship('Post',backref='author',lazy='dynamic')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
	followed = db.relationship(
		'User', secondary=followers,
		primaryjoin=(followers.c.follower_id == id),
		secondaryjoin=(followers.c.followed_id == id),
		backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

	def __repr__(self):
		return '<User {}>'.format(self.username)  

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def avatar(self,size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)



	def follow(self,user):
		if not self.is_following(user):
			self.followed.append(user)

	def unfollow(self,user):
		if self.is_following(user):
			self.followed.remove(user)

	def is_following(self,user):
		  return self.followed.filter(followers.c.followed_id == user.id).count() > 0            

	def followed_posts(self):
		followed = Post.query.join(
			followers, (followers.c.followed_id == Post.user_id)).filter(
				followers.c.follower_id == self.id)
		own = Post.query.filter_by(user_id=self.id)
		return followed.union(own).order_by(Post.timestamp.desc())

	# def get_reset_password_token(self, expires_in=600):
	#     return jwt.encode(
	#         {'reset_password':self.id, 'exp':time() + expires_in},
	#         app.config['SECRET_KEY'],algorithms='HS256')
			
	def get_reset_password_token(self, expires_in=600):
		return jwt.encode({'reset_password': self.id, 'exp': time() + expires_in},app.config['SECRET_KEY'], algorithm='HS256')

	@staticmethod
	def verify_reset_password_token(token):
		try:
			id = jwt.decode(token, app.config['SECRET_KEY'],
							algorithms=['HS256'])['reset_password']
		except:
			return
		return User.query.get(id)

	def is_like(self,post):
		return Like.query.filter(Like.user_id==self.id, Like.post_id==post.id).count()>0

	def like(self, post):
		if not self.is_like(post):
			like = Like(user_id=self.id,post_id=post.id)
			db.session.add(like)

	def unlike(self, post):
		if self.is_like(post):
			# Like(post_id=post.id,user_id=user.id)
			Like.query.filter(Like.user_id==self.id,Like.post_id==post.id).delete()	

	def comment(self,post_id,body):
		comment = Comment(user_id=self.id,post_id=post_id,body=body)
		db.session.add(comment)			
			

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	like = db.relationship('Like',backref='post',lazy='dynamic')

	def __repr__(self):
		return '<Post {}>'.format(self.body)


class Like(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'))


class Comment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

@login.user_loader
def load_user(id):
	return User.query.get(int(id))
		