from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import select

from library import db
from library.models import Transaction
from library.services import LibraryError, issue_book, return_loan

bp = Blueprint('transactions', __name__, url_prefix='/transactions')

FILTERS = {'borrow': 'Issued', 'return': 'Returned', 'payment': 'Payments'}


@bp.route('/')
def index():
    kind = request.args.get('type', '')
    if kind not in FILTERS:
        kind = ''
    page = request.args.get('page', 1, type=int)

    stmt = select(Transaction).order_by(Transaction.id.desc())
    if kind:
        stmt = stmt.where(Transaction.type_of_transaction == kind)

    pagination = db.paginate(stmt, page=page, per_page=current_app.config['PER_PAGE'], error_out=False)
    return render_template('transactions/index.html', pagination=pagination, kind=kind, filters=FILTERS)


@bp.post('/issue')
def issue():
    try:
        book, member = issue_book(request.form.get('book_id', type=int),
                                  request.form.get('member_id', type=int))
        fee = current_app.config['BORROW_FEE']
        flash(f'Issued “{book.title}” to {member.member_name}. The {fee} fee was added to what they owe.', 'success')
    except LibraryError as error:
        flash(str(error), 'error')
    return redirect(url_for('main.desk'))


@bp.post('/return')
def return_book():
    try:
        book, member, paid = return_loan(request.form.get('loan_id', type=int),
                                         request.form.get('paid') == 'on')
        message = f'“{book.title}” was returned by {member.member_name}.'
        if paid:
            message += f' Fee of {paid} collected.'
        flash(message, 'success')
    except LibraryError as error:
        flash(str(error), 'error')
    return redirect(url_for('main.desk'))
