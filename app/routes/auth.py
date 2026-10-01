from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db, limiter
from app.forms import RegistrationForm, LoginForm
from app.models import User
from app.services.audit import log_action

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            role="user",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_action("REGISTER", user_id=user.id)
        flash("Account created. You can now sign in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user is None:
            log_action("FAILED_LOGIN", result="FAILURE", details=f"unknown email: {email}")
            flash("Invalid email or password.", "danger")
            return render_template("login.html", form=form)

        if user.is_locked():
            log_action("FAILED_LOGIN", user_id=user.id, result="FAILURE", details="account locked")
            flash("Account temporarily locked due to repeated failed attempts. Try again later.", "danger")
            return render_template("login.html", form=form)

        if not user.is_active_flag:
            flash("This account has been disabled. Contact an administrator.", "danger")
            return render_template("login.html", form=form)

        if user.check_password(form.password.data):
            user.register_successful_login()
            db.session.commit()
            login_user(user, remember=form.remember.data)
            log_action("LOGIN", user_id=user.id)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        else:
            user.register_failed_login(
                current_app.config["MAX_FAILED_LOGIN_ATTEMPTS"],
                current_app.config["LOCKOUT_MINUTES"],
            )
            db.session.commit()
            log_action("FAILED_LOGIN", user_id=user.id, result="FAILURE")
            flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    log_action("LOGOUT", user_id=current_user.id)
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
