from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField
from wtforms.validators import DataRequired, Optional

class AccountForm(FlaskForm):
    account_type = SelectField('Account Type',
        choices=[('savings', 'Savings Account'), 
                ('checking', 'Checking Account'),
                ('investment', 'Investment Account')],
        validators=[DataRequired()])
    initial_balance = DecimalField('Initial Balance ($)', 
        validators=[DataRequired()])
    currency = SelectField('Currency',
        choices=[('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
                ('GBP', 'GBP - British Pound')],
        validators=[DataRequired()])

class EditAccountForm(FlaskForm):
    status = SelectField('Account Status',
        choices=[('active', 'Active'),
                ('inactive', 'Inactive'),
                ('suspended', 'Suspended')],
        validators=[DataRequired()])