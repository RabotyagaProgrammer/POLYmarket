from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask import session
from app.database import User
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
