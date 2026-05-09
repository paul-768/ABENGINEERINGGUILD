# app/auth/routes.py
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth.forms import LoginForm, RegistrationForm, ForgotPasswordForm, SetNewPasswordForm
from app.models import User
from app.auth import auth_bp
from datetime import datetime
import hashlib
import secrets

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            if user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                flash('Login successful!', 'success')
                return redirect(next_page or url_for('main.dashboard'))
            else:
                flash('Invalid password. Please try again.', 'danger')
        else:
            flash('No account found with this email. Please register first.', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    recovery_key = None
    
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        
        # Generate recovery key for the user
        recovery_key = user.generate_recovery_key()
        
        db.session.add(user)
        db.session.commit()
        
        # Store recovery key in session to show on success page
        session['recovery_key'] = recovery_key
        session['user_email'] = user.email
        
        flash('Registration successful!', 'success')
        return redirect(url_for('auth.registration_success'))
    
    return render_template('auth/register.html', title='Register', form=form, recovery_key=recovery_key)


@auth_bp.route('/registration-success')
def registration_success():
    """Show recovery key to user after registration"""
    recovery_key = session.pop('recovery_key', None)
    user_email = session.pop('user_email', None)
    
    if not recovery_key:
        return redirect(url_for('auth.login'))
    
    return render_template('auth/registration_success.html', 
                          recovery_key=recovery_key,
                          email=user_email)


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))


# ========== RECOVERY KEY PASSWORD RESET ==========
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.verify_recovery_key(form.recovery_key.data):
            # Store user_id in session for password reset
            session['reset_user_id'] = user.id
            session['reset_verified'] = True
            
            flash('Recovery key verified! Please set your new password.', 'success')
            return redirect(url_for('auth.set_new_password'))
        else:
            flash('Invalid email or recovery key. Please try again.', 'danger')
    
    return render_template('auth/forgot_password.html', title='Forgot Password', form=form)


@auth_bp.route('/set-new-password', methods=['GET', 'POST'])
def set_new_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Check if user is verified
    if not session.get('reset_verified') or not session.get('reset_user_id'):
        flash('Please verify your recovery key first.', 'warning')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.get(session['reset_user_id'])
    if not user:
        session.pop('reset_verified', None)
        session.pop('reset_user_id', None)
        flash('Invalid session. Please try again.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = SetNewPasswordForm()
    form.user_id.data = user.id
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        
        # Clear session
        session.pop('reset_verified', None)
        session.pop('reset_user_id', None)
        
        flash('Your password has been successfully reset! Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/set_new_password.html', title='Set New Password', form=form)


# ========== ADD RECOVERY KEY METHOD TO USER MODEL ==========
def generate_recovery_key(self):
    """Generate a unique recovery key for the user"""
    import secrets
    import hashlib
    # Generate a readable recovery key (e.g., ABE-X7K9-2M4P-W8L3)
    parts = []
    for _ in range(3):
        part = secrets.token_urlsafe(4).upper().replace('-', '').replace('_', '')
        parts.append(part)
    recovery_key = f"ABE-{parts[0]}-{parts[1]}-{parts[2]}"
    
    # Hash and store the recovery key
    hashed_key = hashlib.sha256(recovery_key.encode()).hexdigest()
    self.recovery_key_hash = hashed_key
    return recovery_key

def verify_recovery_key(self, key):
    """Verify if the recovery key is correct"""
    if not self.recovery_key_hash:
        return False
    import hashlib
    hashed_key = hashlib.sha256(key.encode()).hexdigest()
    return self.recovery_key_hash == hashed_key

# Note: Add these methods to your User model in models.py