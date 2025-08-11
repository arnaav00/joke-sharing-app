import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g, current_app
from .db import get_db
from flaskr.auth import login_required
from functools import wraps
from flask_login import current_user 

bp = Blueprint('moderation', __name__, url_prefix='/moderation')

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.role != 'Moderator':
            flash('You do not have permission to access this page', 'danger')
            logging.warning('User %s tried to access a moderated route without sufficient permissions', g.user['nickname'])
            return redirect(url_for('index'))
        logging.debug('Moderator %s accessed %s', g.user['nickname'], request.path)
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/users')
@login_required
@moderator_required
def users():
    db = get_db()
    users = db.execute('SELECT id, nickname, email, joke_balance, role FROM user').fetchall()
    logging.info('Moderator %s viewed the user list', g.user['nickname'])
    return render_template('moderation/users.html', users=users)

@bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def edit_user(user_id):
    db = get_db()
    user = db.execute('SELECT id, nickname, email, joke_balance, role FROM user WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        new_balance = request.form.get('joke_balance')
        new_role = request.form.get('role')

        if new_balance and new_balance.isdigit() and int(new_balance) >= 0:
            db.execute('UPDATE user SET joke_balance = ?, role = ? WHERE id = ?',
                       (int(new_balance), new_role, user_id))
            db.commit()
            flash('User information updated successfully', 'success')
            logging.info('Moderator %s updated user %d: joke_balance=%d, role=%s',
                         g.user['nickname'], user_id, int(new_balance), new_role)
        else:
            flash('Invalid joke balance', 'danger')
            logging.warning('Moderator %s attempted invalid update: user_id=%d, joke_balance=%s',
                            g.user['nickname'], user_id, new_balance)
        return redirect(url_for('moderation.users'))

    if user is None:
        flash('User not found', 'danger')
        logging.error('Moderator %s attempted to edit non-existent user %d', g.user['nickname'], user_id)
        return redirect(url_for('moderation.users'))

    logging.debug('Moderator %s is editing user %d', g.user['nickname'], user_id)
    return render_template('moderation/edit_user.html', user=user)

@bp.route('/manage_moderators/<int:user_id>', methods=['POST'])
@login_required
@moderator_required
def manage_moderators(user_id):
    db = get_db()
    moderators_count = db.execute('SELECT COUNT(*) FROM user WHERE role = "Moderator"').fetchone()[0]

    if moderators_count <= 1 and g.user['id'] == user_id:
        flash('You cannot remove the last moderator.', 'danger')
        logging.warning('User %s tried to remove themselves as the last moderator', g.user['nickname'])
        return redirect(url_for('moderation.users'))

    current_role = db.execute('SELECT role FROM user WHERE id = ?', (user_id,)).fetchone()
    if not current_role:
        flash('User not found', 'danger')
        logging.error('Moderator %s attempted to manage non-existent user %d', g.user['nickname'], user_id)
        return redirect(url_for('moderation.users'))

    current_role = current_role['role']
    new_role = 'User' if current_role == 'Moderator' else 'Moderator'
    db.execute('UPDATE user SET role = ? WHERE id = ?', (new_role, user_id))
    db.commit()

    flash(f'User role updated to {new_role}', 'success')
    logging.info('Moderator %s changed user %d role from %s to %s', g.user['nickname'], user_id, current_role, new_role)
    return redirect(url_for('moderation.users'))

@bp.route('/toggle_debug', methods=['POST'])
@moderator_required
def toggle_debug():
    current_app.config['DEBUG'] = not current_app.config['DEBUG']
    status = 'enabled' if current_app.config['DEBUG'] else 'disabled'
    flash(f"Debug logging has been {status}.", 'info')
    logging.info('Moderator %s toggled debug logging to %s', g.user['nickname'], status)
    return redirect(url_for('moderation.users'))
