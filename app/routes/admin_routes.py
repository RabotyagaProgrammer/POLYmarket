from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask import session
from app.database import User, Advertisement
from app.database import db
import hashlib

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def admin_panel():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return redirect(url_for('auth.login'))

    hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    user = User.query.filter_by(refresh_token=hashed_token).first()

    if not user or not user.is_admin:
        flash("Доступ запрещен.")
        return redirect(url_for('main.index'))

    return render_template('admin_panel.html')

@admin_bp.route('/users')
def manage_users():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return redirect(url_for('auth.login'))

    hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    user = User.query.filter_by(refresh_token=hashed_token).first()

    if not user or not user.is_admin:
        flash("Доступ запрещен.")
        return redirect(url_for('main.index'))

    users = User.query.all()
    return render_template('admin_users.html', users=users)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return redirect(url_for('auth.login'))

    hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    admin = User.query.filter_by(refresh_token=hashed_token).first()

    if not admin or not admin.is_admin:
        flash("Доступ запрещен.")
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.tg_contact = request.form['tg_contact']

        old_password = request.form['old_password']
        new_password = request.form['new_password']

        if old_password and new_password:
            # Проверка старого пароля (если хранишь хэш, используешь hashlib)
            old_hash = hashlib.sha256(old_password.encode()).hexdigest()
            if old_hash != user.password_hash:
                return render_template('edit_profile.html', user=user, error="Старый пароль неверный")

            user.password_hash = hashlib.sha256(new_password.encode()).hexdigest()

        db.session.commit()
        flash("Профиль обновлён.")
        return redirect(url_for('admin.manage_users'))

    return render_template('edit_profile.html', user=user)
@admin_bp.route('/users/<int:user_id>/delete')
def delete_user(user_id):
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return redirect(url_for('auth.login'))

    hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    admin = User.query.filter_by(refresh_token=hashed_token).first()

    if not admin or not admin.is_admin:
        flash("Доступ запрещен.")
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("Пользователь удален.")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/add_user', methods=['GET', 'POST'])
def add_user():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return redirect(url_for('auth.login'))

    hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    user = User.query.filter_by(refresh_token=hashed_token).first()

    if not user or not user.is_admin:
        flash("Доступ запрещен.")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        is_admin = bool(request.form.get('is_admin'))

        if password != confirm_password:
            flash("Пароли не совпадают.")
            return render_template('register.html', is_admin_page=True)

        if User.query.filter_by(email=email).first():
            flash("Пользователь с таким email уже существует.")
            return render_template('register.html', is_admin_page=True)

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        new_user = User(name=name, email=email, password_hash=password_hash, is_admin=is_admin)
        db.session.add(new_user)
        db.session.commit()

        flash("Пользователь добавлен.")
        return redirect(url_for('admin.manage_users'))

    return render_template('register.html', is_admin_page=True)


@admin_bp.route('/manage_ads')

def manage_ads():
    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return redirect(url_for('auth.login'))

    hashed_token = hashlib.sha256(refresh_token.encode()).hexdigest()
    user = User.query.filter_by(refresh_token=hashed_token).first()

    if not user or not user.is_admin:
        flash("Доступ запрещен.")
        return redirect(url_for('main.index'))
    ads = Advertisement.query.all()
    return render_template('manage_ads.html', ads=ads)

