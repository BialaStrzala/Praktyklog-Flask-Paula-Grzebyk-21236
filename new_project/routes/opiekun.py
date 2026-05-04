from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import models as models
from datetime import datetime
from functools import wraps

opiekun_bp = Blueprint('opiekun', __name__)

def role_required(rola):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.rola != rola:
                flash('Access denied.')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@opiekun_bp.route('/dashboard')
@role_required('opiekun')
def dashboard():
    return 'Opiekun'