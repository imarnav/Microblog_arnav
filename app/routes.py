from app import app
from flask import render_template
from app.forms import LoginForm, RegistrationForm, CommentForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, followers, Comment
from flask import request, flash, redirect, url_for
from werkzeug.urls import url_parse
from app import db
from datetime import datetime
from app.forms import EditProfileForm, EmptyForm, CommentUpdateForm, PostUpdateForm
from app.forms import PostForm
from app.models import Post
from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email
from app.forms import ResetPasswordForm
from flask import jsonify
from sqlalchemy import desc
# from app.translate import translate



@app.route('/', methods=['GET','POST'])
@app.route('/index',methods=['GET','POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index'))
    # posts = [
    #     {
    #         'author': {'username': 'John'},
    #         'body': 'Beautiful day in Portland!'
    #     },
    #     {
    #         'author': {'username': 'Susan'},
    #         'body': 'The Avengers movie was so cool!'
    #     }
    # ]
    page = request.args.get('page',1,type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html',title='Home Page',form=form,posts=posts.items,
                            next_url=next_url, prev_url=prev_url)


@app.route('/login',methods=['GET',"POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
        
    return render_template('login.html', title='Sign In', form=form)



@app.route('/logout')
def logout():
    logout_user()
    flash('You have been successfully logged out')
    return redirect(url_for('index'))    



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

 
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)   

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()    


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)        



@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))    

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template("index.html", title='Explore', posts=posts.items,
                            next_url=next_url,prev_url=prev_url)


# @app.route('/reset_password_request', methods=['GET','POST'])
# def reset_password_request():
#     if current_user.is_authenticated:
#         return redirect(url_for('index'))
#     form = ResetPasswordRequestForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user:
#             send_password_reset_email(user)
#         flash('Check your mail to reset password')
#         return redirect(url_for('login'))
#     return render_template('reset_password_request.html', title="Reset Password", form=form)
                        
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form) 


@app.route('/translate', methods = ['POST'])
@login_required
def translate_text():
    return jsonify({'text': translate(request.form['text'],request.form['source_language'],request.form['dest_language'])})
                               

@app.route('/like/post')
@login_required
def like():
    post_id = request.args.get('post_id')
    post = Post.query.filter_by(id=post_id).first_or_404()
    current_user.like(post)
    db.session.commit()
    return jsonify({'success':True}),200,{'ContentType':'application/json'}         
    # if action=='like':
    #     current_user.like(post)
    #     db.session.commit()
    # else:
    #     current_user.unlike(post)    
    #     db.session.commit()
    # return redirect(request.referrer)        

@app.route('/unlike/post')
@login_required
def unlike():
    post_id = request.args.get('post_id')
    post = Post.query.filter_by(id=post_id).first_or_404()
    current_user.unlike(post)    
    db.session.commit()
    return jsonify({'success':True}),200,{'ContentType':'application/json'}     


@app.route('/test/<username>')
@login_required
def follower_detail(username):
    user = User.query.filter_by(username=username).first_or_404()
    # a = followers.query.filter(followers.c.followed_id==user.id).all()
    a = (user.followers.all())
    return render_template('test.html',follower_list = a,user=user)

@app.route('/test1/<username>')
@login_required
def following_detail(username):
    user = User.query.filter_by(username=username).first_or_404()
    # b = user.followed.filter(followers.c.follower_id==user.id).all()
    b = (user.followed.all())
    return render_template('test1.html',followed_list = b,user=user)


@app.route('/comment/<post_id>', methods=['GET','POST'])
@login_required
def add_comment(post_id):
    form = CommentForm()
    post = Post.query.filter_by(id=post_id).first_or_404()
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.timestamp.desc()).all()
    count = Comment.query.filter_by(post_id=post_id).count()
    # username = User.query.filter_by()
    if form.validate_on_submit():
        current_user.comment(post_id=post.id,body=form.comment.data)
        # comment = Comment(body=form.comment.data, user_id=current_user.id, post_id=post_id)
        db.session.commit()
        return redirect(request.referrer)
    return render_template('comment.html',form=form,title='Add Comment',comments=comments,count=count,current_user=current_user)    


@app.route('/delete/<comment_id>')
@login_required
def delete(comment_id):
    delete = Comment.query.filter_by(id=comment_id).first_or_404()
    db.session.delete(delete)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/post/delete/<post_id>')
@login_required
def delete_post(post_id):
    comments = Comment.query.filter_by(post_id=post_id).all()
    for comment in comments:
        db.session.delete(comment)
    delete = Post.query.filter_by(id=post_id).first_or_404()
    db.session.delete(delete)
    db.session.commit()
    return redirect(request.referrer)


@app.route('/update/comment/<comment_id>', methods=['GET','POST'])
@login_required
def update_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first_or_404()
    form = CommentUpdateForm(comment=comment.body)
    # form.comment.data = comment.body
    if form.validate_on_submit():
        comment.body = form.comment.data
        db.session.commit()
        flash("Comment is updated!!")
        return redirect(url_for('index'))


    return render_template('update_comment.html',form=form,title='Update Comment')    


@app.route('/update/post/<post_id>',methods=['GET','POST'])
@login_required
def update_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    form = PostUpdateForm(post=post.body)
    if form.validate_on_submit():
        post.body = form.post.data
        db.session.commit()
        flash("Post is updated now!!")
        return redirect(url_for('index'))

    return render_template('update_post.html',form=form,title='Post updated')
        
