from datetime import date

from library import db


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    member_name = db.Column(db.String, nullable=False, unique=True)  # the member's unique username
    phone_number = db.Column(db.String, nullable=False, unique=True)
    to_pay = db.Column(db.Integer, nullable=False, default=0)        # fees the member still owes
    total_paid = db.Column(db.Integer, nullable=False, default=0)    # fees the member has paid so far

    loans = db.relationship('Loan', back_populates='member', lazy='selectin')


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    isbn = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)         # copies the library owns
    borrow_stock = db.Column(db.Integer, nullable=False, default=0)  # copies on the shelf right now
    member_count = db.Column(db.Integer, nullable=False, default=0)  # how many times it has been issued
    returned = db.Column(db.Boolean, default=False)                  # unused, kept so existing databases still match

    loans = db.relationship('Loan', back_populates='book')


class Loan(db.Model):
    """One copy of a book currently out with a member. The row is removed when it is returned."""
    __tablename__ = 'book_borrow'

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column('member', db.Integer, db.ForeignKey('member.id'), nullable=False, key='member_id')
    book_id = db.Column('book', db.Integer, db.ForeignKey('book.id'), nullable=False, key='book_id')

    member = db.relationship('Member', back_populates='loans')
    book = db.relationship('Book', back_populates='loans')


Book_borrowed = Loan  # the old name, in case other code still imports it


class Transaction(db.Model):
    BORROW = 'borrow'
    RETURN = 'return'
    PAYMENT = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String)
    member_name = db.Column(db.String)
    type_of_transaction = db.Column(db.String(length=7), nullable=False)
    date = db.Column(db.Date, default=date.today)
    amount = db.Column(db.Integer, default=0)
