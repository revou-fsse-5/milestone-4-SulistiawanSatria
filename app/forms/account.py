from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, StringField
from wtforms.validators import DataRequired, NumberRange

class AccountForm(FlaskForm):
    account_type = SelectField(
        'Account Type',
        choices=[
            ('savings', 'Savings Account'),
            ('checking', 'Checking Account'),
            ('investment', 'Investment Account')
        ],
        validators=[DataRequired()]
    )
    initial_balance = DecimalField(
        'Initial Balance',
        validators=[
            DataRequired(),
            NumberRange(min=0, message="Initial balance must be positive")
        ]
    )
    currency = SelectField(
        'Currency',
        choices=[
            ('USD', 'USD - US Dollar'),
            ('EUR', 'EUR - Euro'),
            ('GBP', 'GBP - British Pound')
        ],
        default='USD'
    )