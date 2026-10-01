from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (StringField, PasswordField, SubmitField, SelectField,
                      BooleanField)
from wtforms.validators import (DataRequired, Email, Length, EqualTo,
                                 ValidationError)

from app.models import User


class RegistrationForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, message="Use at least 8 characters.")],
    )
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with this email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class UploadForm(FlaskForm):
    file = FileField("Document", validators=[FileRequired()])
    submit = SubmitField("Upload")


class ShareForm(FlaskForm):
    recipient_email = StringField("Recipient email", validators=[DataRequired(), Email()])
    permission = SelectField(
        "Permission",
        choices=[("VIEW", "View only"), ("DOWNLOAD", "View & download")],
        default="VIEW",
    )
    expires_in = SelectField(
        "Expires",
        choices=[
            ("1h", "1 hour"),
            ("1d", "1 day"),
            ("7d", "7 days"),
            ("30d", "30 days"),
            ("never", "Never"),
        ],
        default="7d",
    )
    submit = SubmitField("Share document")

    def validate_recipient_email(self, field):
        if not User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("No user with this email is registered on the platform.")
