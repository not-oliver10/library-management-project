from flask import Blueprint, current_app, redirect, render_template, request, url_for
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from library import db
from library.models import Book, Loan, Member, Transaction

bp = Blueprint('main', __name__)


@bp.route('/')
@bp.route('/home')
def desk():
    limit = current_app.config['DEBT_LIMIT']

    available_books = Book.query.filter(Book.borrow_stock > 0).order_by(Book.title).all()
    eligible_members = Member.query.filter(Member.to_pay < limit).order_by(Member.name).all()
    blocked_count = Member.query.filter(Member.to_pay >= limit).count()
    loans = (Loan.query.options(joinedload(Loan.book), joinedload(Loan.member))
             .order_by(Loan.id.desc()).all())
    recent = Transaction.query.order_by(Transaction.id.desc()).limit(8).all()

    stats = {
        'titles': db.session.scalar(select(func.count(Book.id))),
        'on_shelf': db.session.scalar(select(func.coalesce(func.sum(Book.borrow_stock), 0))),
        'on_loan': len(loans),
        'members': db.session.scalar(select(func.count(Member.id))),
        'dues': db.session.scalar(select(func.coalesce(func.sum(Member.to_pay), 0))),
    }

    return render_template(
        'desk.html', books=available_books, members=eligible_members, loans=loans,
        recent=recent, stats=stats, blocked_count=blocked_count,
        selected_book=request.args.get('book', type=int),
        selected_member=request.args.get('member', type=int),
        selected_loan=request.args.get('loan', type=int))


@bp.route('/search')
def search():
    """Old search URL. Searching now happens on the Books page."""
    return redirect(url_for('books.index', q=request.args.get('q', '')))


def _ranked(rows, label, value):
    """Turn rows into {label, value, pct} dicts, where pct is the bar length relative to the top row."""
    top = max((value(row) for row in rows), default=0) or 1
    return [{'label': label(row), 'value': value(row), 'pct': round(value(row) * 100 / top)} for row in rows]


@bp.route('/reports')
def reports():
    top_books = db.session.execute(
        select(Book).where(Book.member_count > 0)
        .order_by(Book.member_count.desc(), Book.title).limit(10)).scalars().all()
    top_members = db.session.execute(
        select(Member).where(Member.total_paid > 0)
        .order_by(Member.total_paid.desc(), Member.name).limit(10)).scalars().all()

    totals = {
        'titles': db.session.scalar(select(func.count(Book.id))),
        'members': db.session.scalar(select(func.count(Member.id))),
        'issued': db.session.scalar(select(func.coalesce(func.sum(Book.member_count), 0))),
        'collected': db.session.scalar(select(func.coalesce(func.sum(Member.total_paid), 0))),
        'dues': db.session.scalar(select(func.coalesce(func.sum(Member.to_pay), 0))),
    }

    return render_template(
        'reports.html', totals=totals,
        popular_books=_ranked(top_books, lambda b: b.title, lambda b: b.member_count),
        top_payers=_ranked(top_members, lambda m: f'{m.name} ({m.member_name})', lambda m: m.total_paid))
