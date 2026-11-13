"""The library's rules for issuing, returning and paying, kept apart from the web layer."""
from datetime import date

from flask import current_app

from library import db
from library.models import Book, Loan, Member, Transaction


class LibraryError(Exception):
    """Raised when an action breaks a library rule. The message is safe to show to staff."""


def issue_book(book_id, member_id):
    if not book_id or not member_id:
        raise LibraryError('Choose both a book and a member.')

    # Lock the rows so two desks can't hand out the last copy at the same moment.
    book = db.session.get(Book, book_id, with_for_update=True)
    member = db.session.get(Member, member_id, with_for_update=True)
    if book is None or member is None:
        raise LibraryError('That book or member no longer exists.')

    limit = current_app.config['DEBT_LIMIT']
    fee = current_app.config['BORROW_FEE']

    if book.borrow_stock <= 0:
        raise LibraryError(f'No copies of “{book.title}” are on the shelf.')
    if member.to_pay >= limit:
        raise LibraryError(f'{member.member_name} owes {member.to_pay} and can’t borrow until they pay.')
    if any(loan.book_id == book.id for loan in member.loans):
        raise LibraryError(f'{member.member_name} already has a copy of “{book.title}”.')

    book.borrow_stock -= 1
    book.member_count += 1
    member.to_pay += fee
    db.session.add(Loan(book=book, member=member))
    db.session.add(Transaction(
        book_name=book.title, member_name=member.member_name,
        type_of_transaction=Transaction.BORROW, amount=0, date=date.today()))
    db.session.commit()
    return book, member


def return_loan(loan_id, fee_paid):
    loan = db.session.get(Loan, loan_id) if loan_id else None
    if loan is None:
        raise LibraryError('Choose a book to return. It may already have been returned.')

    book, member = loan.book, loan.member
    paid = 0
    if fee_paid:
        # Never take more than the member owes.
        paid = min(current_app.config['BORROW_FEE'], member.to_pay)

    member.to_pay -= paid
    member.total_paid += paid
    book.borrow_stock += 1
    db.session.delete(loan)
    db.session.add(Transaction(
        book_name=book.title, member_name=member.member_name,
        type_of_transaction=Transaction.RETURN, amount=paid, date=date.today()))
    db.session.commit()
    return book, member, paid


def record_payment(member_id, amount):
    member = db.session.get(Member, member_id, with_for_update=True) if member_id else None
    if member is None:
        raise LibraryError('That member no longer exists.')
    if not amount or amount < 1:
        raise LibraryError('Enter an amount of 1 or more.')
    if amount > member.to_pay:
        raise LibraryError(f'{member.member_name} only owes {member.to_pay}.')

    member.to_pay -= amount
    member.total_paid += amount
    db.session.add(Transaction(
        book_name=None, member_name=member.member_name,
        type_of_transaction=Transaction.PAYMENT, amount=amount, date=date.today()))
    db.session.commit()
    return member
