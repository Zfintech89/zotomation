# auth.py
from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # For API requests
        if request.is_json:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            # Input validation
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return jsonify({'error': 'Username already exists'}), 409
            
            # Create new user
            new_user = User(username=username)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Set session
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            
            return jsonify({
                'message': 'User registered successfully',
                'user': new_user.to_dict()
            }), 201
        
        # For form submissions
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Username and password are required')
                return redirect(url_for('auth.register'))
            
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists')
                return redirect(url_for('auth.register'))
            
            new_user = User(username=username)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            
            return redirect(url_for('index'))
    
    # GET request - show registration form
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # For API requests
        if request.is_json:
            data = request.json
            username = data.get('username')
            password = data.get('password')
            
            # Input validation
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            # Find user
            user = User.query.filter_by(username=username).first()
            
            # Validate password
            if not user or not user.check_password(password):
                return jsonify({'error': 'Invalid username or password'}), 401
            
            # Set session
            session['user_id'] = user.id
            session['username'] = user.username
            
            return jsonify({
                'message': 'Login successful',
                'user': user.to_dict()
            })
        
        # For form submissions
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Username and password are required')
                return redirect(url_for('auth.login'))
            
            user = User.query.filter_by(username=username).first()
            
            if not user or not user.check_password(password):
                flash('Invalid username or password')
                return redirect(url_for('auth.login'))
            
            session['user_id'] = user.id
            session['username'] = user.username
            
            return redirect(url_for('dashboard'))
    
    # GET request - show login form
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out')
    return redirect(url_for('auth.login'))

@auth_bp.route('/user')
@login_required
def get_current_user():
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    
    if not user:
        session.pop('user_id', None)
        session.pop('username', None)
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})