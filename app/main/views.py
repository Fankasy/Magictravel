#!/usr/bin/python
#-*- coding: utf-8 -*-
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response
from flask.ext.login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm,\
    CommentForm,AddviewForm,ViewguidesForm,EditViewForm
from .. import db
from ..models import Permission, Role, User, Comment,View,Viewguide
from ..decorators import admin_required, permission_required


@main.route('/', methods=['GET', 'POST'])
def index():

    page = request.args.get('page', 1, type=int)

    pagination = View.query.order_by(View.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    views = pagination.items
    return render_template('index.html',  views=views,
                            pagination=pagination)

@main.route('/addview', methods=['GET', 'POST'])
@login_required
@admin_required
def addview():
    form=AddviewForm()
    if current_user.is_administrator() and \
        form.validate_on_submit():
        view=View(name=form.name.data,location=form.location.data,address=form.address.data,opentime=form.opentime.data
        ,about_view=form.about_view.data)
        db.session.add(view)
        return redirect(url_for('.index'))

    return render_template('addview.html', form=form)



@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.viewguides.order_by(Viewguide.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    viewguides = pagination.items
    return render_template('user.html', user=user, viewguides=viewguides,
                           pagination=pagination)

@main.route('/view/<name>',methods=['GET', 'POST'])
def view(name):
    view = View.query.filter_by(name=name).first_or_404()
    form = ViewguidesForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        viewguide = Viewguide(body=form.body.data,
                          view=view,
                          author=current_user._get_current_object())
        db.session.add(viewguide)
        flash('您的攻略已发表.')
        return redirect(url_for('.view', name=view.name, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (view.viewguides.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = view.viewguides.order_by(Viewguide.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    viewguides = pagination.items
    return render_template('views.html', view=view, viewguides=viewguides,form=form,
                           pagination=pagination)



@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('您的个人信息已被更新.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('用户信息已被更新.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

@main.route('/edit-view/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_view_admin(id):
    view = View.query.get_or_404(id)
    form = EditViewForm(view=view)
    if form.validate_on_submit():
        view.name = form.name.data
        view.address = form.address.data
        view.location = form.location.data
        view.opentime = form.opentime.data
        view.about_view=form.about_view.data
        db.session.add(view)
        flash('景点信息已被更新.')
        return redirect(url_for('.view', name=view.name))
    form.name.data = view.name
    form.address.data = view.address
    form.location.data = view.location
    form.opentime.data = view.opentime
    return render_template('edit_view.html', form=form, view=view)





@main.route('/viewguide/<int:id>', methods=['GET', 'POST'])
def viewguide(id):
    viewguide = Viewguide.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          viewguide=viewguide,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('您的评论已发表.')
        return redirect(url_for('.viewguide', id=viewguide.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (viewguide.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = viewguide.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('viewguide.html', viewguides=[viewguide], form=form,
                           comments=comments, pagination=pagination)



@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    viewguide = Viewguide.query.get_or_404(id)
    if current_user != viewguide.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = ViewguidesForm()
    if form.validate_on_submit():
        viewguide.body = form.body.data
        db.session.add(viewguide)
        flash('旅游攻略已被更新.')
        return redirect(url_for('.viewguide', id=viewguide.id))
    form.body.data = viewguide.body
    return render_template('edit_viewguide.html', form=form)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效用户.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('你已经关注该用户.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('你现在已经关注了 %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效用户.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('你已经关注该用户.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('你现在已不再关注 %s了 .' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效用户.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('无效用户.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))
