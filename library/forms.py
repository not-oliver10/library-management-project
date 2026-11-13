from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, Regexp, ValidationError

from library.models import Book, Member


def _strip(value):
    return value.strip() if isinstance(value, str) else value


class MemberForm(FlaskForm):
    """Used to add a member and to edit one. Pass member=<the member being edited> when editing."""

    name = StringField('Full name', filters=[_strip], validators=[
        DataRequired('Enter the member’s full name.'),
        Length(min=2, max=60, message='Use between 2 and 60 characters.')])
    member_name = StringField('Username', filters=[_strip], validators=[
        DataRequired('Choose a username.'),
        Length(min=2, max=30, message='Use between 2 and 30 characters.'),
        Regexp(r'^\S+$', message='A username can’t contain spaces.')])
    phone_number = StringField('Phone number', filters=[_strip], validators=[
        DataRequired('Enter a phone number.'),
        Regexp(r'^[0-9+()\-\s]{6,20}$', message='Use 6 to 20 digits. Spaces, +, - and brackets are fine.')])

    def __init__(self, *args, member=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.member = member

    def validate_member_name(self, field):
        if self._is_taken(Member.member_name, field.data):
            raise ValidationError('Another member already uses this username.')

    def validate_phone_number(self, field):
        if self._is_taken(Member.phone_number, field.data):
            raise ValidationError('Another member already uses this phone number.')

    def _is_taken(self, column, value):
        query = Member.query.filter(func.lower(column) == (value or '').lower())
        if self.member is not None:
            query = query.filter(Member.id != self.member.id)
        return query.first() is not None


class BookForm(FlaskForm):
    """Used to add a book and to edit one. Pass book=<the book being edited> when editing."""

    title = StringField('Title', filters=[_strip], validators=[
        DataRequired('Enter the book’s title.'), Length(max=255, message='Use 255 characters or fewer.')])
    author = StringField('Author', filters=[_strip], validators=[
        DataRequired('Enter the author’s name.'), Length(max=255, message='Use 255 characters or fewer.')])
    isbn = StringField('ISBN', filters=[_strip], validators=[
        DataRequired('Enter the ISBN.'), Length(max=32, message='Use 32 characters or fewer.')])
    stock = IntegerField('Total copies', validators=[
        InputRequired('Enter how many copies the library owns.'),
        NumberRange(min=0, max=100000, message='Enter a whole number from 0 to 100000.')])

    def __init__(self, *args, book=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.book = book

    def validate_author(self, field):
        query = Book.query.filter(
            func.lower(Book.title) == (self.title.data or '').lower(),
            func.lower(Book.author) == (field.data or '').lower())
        if self.book is not None:
            query = query.filter(Book.id != self.book.id)
        if query.first() is not None:
            raise ValidationError('This title by this author is already in the catalog.')

    def validate_stock(self, field):
        if self.book is not None and field.data is not None:
            out = len(self.book.loans)
            if field.data < out:
                raise ValidationError(f'{out} copies are out on loan, so the total can’t be lower than {out}.')


class ImportForm(FlaskForm):
    title = StringField('Title to search for', filters=[_strip], validators=[
        DataRequired('Enter a title to search for.'), Length(max=100, message='Use 100 characters or fewer.')])
    pages = SelectField('How many books', coerce=int, default=1, choices=[
        (1, 'Up to 20 books'), (2, 'Up to 40 books'), (3, 'Up to 60 books')])
