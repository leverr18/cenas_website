from flask import Blueprint, render_template, flash, redirect, url_for
from .forms import LoginForm, SignUpForm, PasswordChangeForm
from .models import Customer
from . import db
from .__init__ import ALLOWED_CODE
from flask_login import login_user, login_required, logout_user
from sqlalchemy import func

auth = Blueprint('auth', __name__)

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm()
    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        username = (form.username.data or email.split("@")[0]).strip()
        password1 = form.password1.data or ""
        password2 = form.password2.data or ""
        registration_code = form.registration_code.data

        if registration_code != ALLOWED_CODE:
            flash("Invalid employee registration code.", "error")
            return render_template('signup.html', form=form)

        if password1 != password2:
            flash("Passwords do not match.", "error")
            return render_template('signup.html', form=form)

        # Case-insensitive existence check
        exists = Customer.query.filter(func.lower(Customer.email) == email).first()
        if exists:
            flash('Account Not Created! Email already exists.', 'error')
            return redirect(url_for('auth.login'))

        try:
            new_customer = Customer(
                email=email,
                username=username,
            )
            # uses Customer.password setter (PBKDF2 if you updated the model)
            new_customer.password = password2

            db.session.add(new_customer)
            db.session.commit()
            flash('Account Created Successfully, You can now Login', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()  # prevent session lock
            print(e)
            flash('Account Not Created! Something went wrong.', 'error')

        # optional: clear fields
        form.email.data = ''
        form.username.data = ''
        form.password1.data = ''
        form.password2.data = ''

    return render_template('signup.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = (form.email.data or "").strip().lower()
        password = form.password.data or ""

        # Case-insensitive lookup
        customer = Customer.query.filter(func.lower(Customer.email) == email).first()

        if customer and customer.verify_password(password=password):
            login_user(customer)
            return redirect(url_for('views.dashboard'))

        # fallthrough: no user or wrong password
        flash('Incorrect Email or Password', 'error')

    return render_template('login.html', form=form)


@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def log_out():
    logout_user()
    return redirect(url_for('auth.login'))


