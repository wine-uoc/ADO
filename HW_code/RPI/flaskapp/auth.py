"""Routes for user authentication."""
from flask import current_app as app
from flask import redirect, render_template, flash, Blueprint, request, url_for
from flask_login import current_user, login_user, logout_user

from . import login_manager
from .assets import compile_auth_assets
from .backend.mainflux_provisioning import register_node_backend
from .control import sign_up_database, validate_user, delete_tables_entries, validate_email
from .forms import LoginForm, SignupForm, ResetForm
from .models import User

# Blueprint Configuration
auth_bp = Blueprint('auth_bp', __name__,
                    template_folder='templates',
                    static_folder='static')
compile_auth_assets(app)


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    User sign-up page.

    GET: Serve sign-up page.
    POST: If submitted credentials are valid:
    add user to 'userdata' table at db,
    initialize 'nodeconfig' table at db,
    create 'tokens' table at db;
    redirect user to the logged-in node configuration page.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))  # Bypass if user is logged in

    signup_form = SignupForm()
    if request.method == 'POST' and signup_form.validate_on_submit():
        # Initialize user and all associated tables in db in RPI
        error_msg, user, node_id = sign_up_database(signup_form.name.data,
                                                    signup_form.org.data,
                                                    signup_form.email.data,
                                                    signup_form.password.data,
                                                    signup_form.device.data)
        if not error_msg:
            login_user(user)  # Log in as newly created user (first, to allow queries using current_user)
            # User data provisioning to backend
            error_msg = register_node_backend(signup_form.name.data,
                                              signup_form.org.data,
                                              signup_form.email.data,
                                              signup_form.password.data,
                                              node_id)
            if not error_msg:
                # Registration OK, app log in and proceed
                return redirect(url_for('main_bp.dashboard'))
            logout_user()
            delete_tables_entries()

        flash(error_msg)
        return redirect(url_for('auth_bp.signup'))

    flash("This registration procedure will link the node to the account provided. A new account will be created "
          "if you don't have one.")
    return render_template('signup.jinja2',
                           title='Create account - ADO',
                           form=signup_form,
                           template='signup-page',
                           body="Sign up for a user account.")


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login page.

    GET: Serve Log-in page.
    POST: If form is valid and new user creation succeeds, redirect user to the logged-in homepage.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))  # Bypass if user is logged in

    login_form = LoginForm()
    if request.method == 'POST' and login_form.validate_on_submit():
        # Validate user
        user = validate_user(login_form.email.data,
                             login_form.password.data)
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main_bp.dashboard'))
        flash('Invalid email/password combination.')
        return redirect(url_for('auth_bp.login'))

    return render_template('login.jinja2',
                           form=login_form,
                           title='Log in - ADO',
                           template='login-page')

@auth_bp.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    """
    User reset password.

    GET: Serve password reset page.
    POST: If form is valid and email checks, send user a password reset url.
    """
    pass_reset_form = ResetForm()
    if request.method == 'POST' and pass_reset_form.validate_on_submit():
        # Validate user
        user = validate_email(login_form.email.data)
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main_bp.dashboard'))
        flash('This node is registered to a different email address')
        return redirect(url_for('auth_bp.login'))

    return render_template('forgot.jinja2',
                           form=pass_reset_form,
                           title='Password Reset - ADO',
                           template='login-page')

@login_manager.user_loader
def load_user(user_id):
    """Check if user is logged-in on every page load."""
    if user_id is not None:
        return User.query.get(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    """Redirect unauthorized users to Login page."""
    flash('You must be logged in to view the page.')
    return redirect(url_for('auth_bp.login'))
