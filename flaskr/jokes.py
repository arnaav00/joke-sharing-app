import logging
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, session
)
from werkzeug.exceptions import abort
from flaskr.auth import login_required, role_required
from flaskr.db import get_db

bp = Blueprint('jokes', __name__, url_prefix='/jokes')

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG)

@bp.route('/leave', methods=('GET', 'POST'))
def leave():
    if g.role == 'Moderator':
        flash('Moderators are not allowed to leave a joke', 'error')
        logging.warning('Moderator %s tried to leave a joke', g.user['nickname'])
        return redirect(url_for('jokes.list'))  
    user_id = g.user['id']
    db = get_db()
    joke_balance = db.execute('SELECT joke_balance FROM user WHERE id = ?', (user_id,)).fetchone()
    joke_balance = joke_balance[0] if joke_balance else 0

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'A joke needs a title. You know, for pizzazz.'
        elif len(title.split()) > 10:
            error = 'We have a 10 word limit for titles here.'
        elif len(body.split()) > 100:
            error = 'Hmm, that joke was too long. Try to keep it under 100 words.'
        elif not body:
            error = 'Nobody likes no body. And your joke needs one!'

        existing_joke = db.execute('SELECT id FROM joke WHERE title = ? AND user_id = ?', (title, g.user['id'])).fetchone()
        if existing_joke is not None:
            error = 'You have already used this title.'

        if error is None:
            db.execute('INSERT INTO joke (title, body, user_id) VALUES (?, ?, ?)', (title, body, user_id))
            db.execute('UPDATE user SET joke_balance = joke_balance + 1 WHERE id = ?', (user_id,))
            db.commit()
            logging.info('User %s added a joke with title "%s"', g.user['nickname'], title)
            return redirect(url_for('jokes.my_jokes'))
        
        flash(error)
        logging.warning('User %s encountered error while leaving joke: %s', g.user['nickname'], error)

    return render_template('jokes/leave.html', joke_balance=joke_balance, title='')

@bp.route('/my_jokes')
@login_required
def my_jokes():
    db = get_db()
    user_id = g.user['id']
    joke_balance = db.execute('SELECT joke_balance FROM user WHERE id = ?', (user_id,)).fetchone()
    joke_balance = joke_balance[0] if joke_balance else 0
    jokes = db.execute('SELECT id, title, body, created, rating FROM joke WHERE user_id = ?', (user_id,)).fetchall()

    logging.debug('User %s is viewing their own jokes', g.user['nickname'])

    return render_template('jokes/my_jokes.html', jokes=jokes, joke_balance=joke_balance, title='My Jokes')

@bp.route('/list')
@login_required
def list():
    db = get_db()
    user_id = g.user['id']
    joke_balance = db.execute('SELECT joke_balance FROM user WHERE id = ?', (user_id,)).fetchone()
    joke_balance = joke_balance[0] if joke_balance else 0

    if joke_balance == 0 and g.role != 'Moderator':
        flash('Oops! You\'re all out of joke balance. Leave another to view more.')
        logging.warning('User %s tried to view jokes with no remaining joke balance', g.user['nickname'])
        return redirect(url_for('jokes.my_jokes'))

    jokes = db.execute('SELECT j.id, j.title, j.body, j.rating, u.nickname, j.user_id FROM joke j JOIN user u ON j.user_id = u.id WHERE j.user_id != ?', (user_id,)).fetchall()
    logging.debug('User %s is viewing a list of jokes', g.user['nickname'])

    return render_template('jokes/list.html', jokes=jokes, joke_balance=joke_balance, title='Available Jokes')

@bp.route('/view/<int:joke_id>', methods=('GET', 'POST'))
@login_required
def view(joke_id):
    db = get_db()
    user_id = g.user['id']
    
    joke_balance = db.execute('SELECT joke_balance FROM user WHERE id = ?', (user_id,)).fetchone()
    joke_balance = joke_balance[0] if joke_balance else 0

    if joke_balance == 0 and g.role != 'Moderator':
        flash('Oops! You\'re all out of joke balance. Leave another to view more.')
        logging.warning('User %s tried to view joke %d with no remaining joke balance', g.user['nickname'], joke_id)
        return redirect(url_for('jokes.my_jokes'))
    
    joke = db.execute('SELECT j.id, j.title, j.body, j.rating, j.user_id, u.nickname, j.created FROM joke j JOIN user u ON j.user_id = u.id WHERE j.id = ?', (joke_id,)).fetchone()

    if joke is None:
        abort(404, f"Joke id {joke_id} doesn't exist.")
        logging.error('User %s tried to view a non-existent joke with id %d', g.user['nickname'], joke_id)
    
    if joke['user_id'] != user_id:
        joke_balance -= 1
        if joke_balance > 0:
            db.execute('UPDATE user SET joke_balance = joke_balance - 1 WHERE id = ?', (user_id,))
            db.commit()
        else:
            db.execute('UPDATE user SET joke_balance = 0 WHERE id = ?', (user_id,))
            db.commit()

    if request.method == 'POST' and g.user['id'] != joke['user_id']:
        rating = float(request.form['rating'])
        current_rating = db.execute('SELECT rating FROM joke WHERE id = ?', (joke_id,)).fetchone()[0]
        new_rating = rating
        if current_rating != 0:
            new_rating = round((current_rating + rating) / 2, 1)
        db.execute('UPDATE joke SET rating = ? WHERE id = ?', (new_rating, joke_id))
        db.commit()

        flash('Your rating has been recorded.')
        logging.info('User %s rated joke %d with a rating of %f', g.user['nickname'], joke_id, new_rating)

        joke_balance += 1
        db.execute('UPDATE user SET joke_balance = joke_balance + 1 WHERE id = ?', (user_id,))
        db.commit()
        if joke_balance == 0 and g.role != 'Moderator':
            flash('Oops! You\'re all out of joke balance. Leave another to view more.')
            return redirect(url_for('jokes.my_jokes'))
        else:
            return redirect(url_for('jokes.list', joke_id=joke_id, joke_balance=joke_balance, title=' '))

    return render_template('jokes/view.html', joke=joke, joke_balance=joke_balance, title=' ')

@bp.route('/edit/<int:joke_id>', methods=('GET', 'POST'))
@login_required
def edit_joke(joke_id):
    user_id = g.user['id']
    db = get_db()

    joke = db.execute('SELECT title, body, user_id FROM joke WHERE id = ?', (joke_id,)).fetchone()

    if joke is None:
        flash("Joke not found.")
        logging.warning('User %s tried to edit a non-existent joke with id %d', g.user['nickname'], joke_id)
        return redirect(url_for('jokes.list'))

    if joke['user_id'] != user_id and g.role != 'Moderator':
        flash("You can only edit your own jokes.")
        logging.warning('User %s tried to edit a joke they don\'t own', g.user['nickname'])
        return redirect(url_for('jokes.my_jokes'))

    title, body = joke['title'], joke['body']

    if request.method == 'POST':
        new_body = request.form['body']
        error = None

        if len(new_body.split()) > 100:
            error = 'Joke body must be no more than 100 words.'
        elif not new_body:
            error = 'Joke body is required.'

        if error is None:
            db.execute('UPDATE joke SET body = ? WHERE id = ? AND user_id = ? OR ? = "Moderator"', (new_body, joke_id, user_id, g.role))
            db.commit()
            flash("That joke has been updated!")
            logging.info('User %s updated joke %d', g.user['nickname'], joke_id)
            if g.role == 'Moderator':
                return redirect(url_for('jokes.list'))
            else:
                return redirect(url_for('jokes.my_jokes'))

        flash(error)

    return render_template('jokes/edit.html', title=title, body=body, joke_id=joke_id)

@bp.route('/delete/<int:joke_id>', methods=['POST'])
@login_required
def delete(joke_id):
    user_id = g.user['id']
    db = get_db()

    joke = db.execute('SELECT id, user_id FROM joke WHERE id = ?', (joke_id,)).fetchone()

    if joke is None:
        flash('Joke not found.')
        logging.warning('User %s tried to delete a non-existent joke with id %d', g.user['nickname'], joke_id)
        if g.role == 'Moderator':
            return redirect(url_for('jokes.list'))
        else:
            return redirect(url_for('jokes.my_jokes'))

    if joke['user_id'] != user_id and g.role != 'Moderator':
        flash('You can only delete your own jokes.')
        logging.warning('User %s tried to delete a joke they don\'t own', g.user['nickname'])
        return redirect(url_for('jokes.my_jokes'))

    db.execute('DELETE FROM joke WHERE id = ?', (joke_id,))
    db.commit()
    logging.info('User %s deleted joke %d', g.user['nickname'], joke_id)

    if g.role == 'Moderator':
        return redirect(url_for('jokes.list'))
    else:
        return redirect(url_for('jokes.my_jokes'))
