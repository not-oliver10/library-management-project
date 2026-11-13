import requests
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import or_, select

from library import db
from library.forms import BookForm, ImportForm
from library.models import Book

bp = Blueprint('books', __name__, url_prefix='/books')


def _like_pattern(term):
    """Build a LIKE pattern from what the user typed, treating % and _ as ordinary characters."""
    escaped = term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f'%{escaped}%'


@bp.route('/')
def index():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    stmt = select(Book).order_by(Book.title, Book.id)
    if q:
        pattern = _like_pattern(q)
        stmt = stmt.where(or_(
            Book.title.ilike(pattern, escape='\\'),
            Book.author.ilike(pattern, escape='\\'),
            Book.isbn.ilike(pattern, escape='\\')))

    pagination = db.paginate(stmt, page=page, per_page=current_app.config['PER_PAGE'], error_out=False)
    return render_template('books/index.html', pagination=pagination, q=q)


@bp.route('/new', methods=['GET', 'POST'])
def create():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(title=form.title.data, author=form.author.data, isbn=form.isbn.data,
                    stock=form.stock.data, borrow_stock=form.stock.data)
        db.session.add(book)
        db.session.commit()
        flash(f'Added “{book.title}”.', 'success')
        return redirect(url_for('books.index'))
    return render_template('books/form.html', form=form, book=None)


@bp.route('/<int:book_id>/edit', methods=['GET', 'POST'])
def edit(book_id):
    book = db.get_or_404(Book, book_id)
    form = BookForm(obj=book, book=book)
    if form.validate_on_submit():
        on_loan = len(book.loans)
        book.title = form.title.data
        book.author = form.author.data
        book.isbn = form.isbn.data
        book.stock = form.stock.data
        book.borrow_stock = form.stock.data - on_loan  # copies still on the shelf
        db.session.commit()
        flash(f'Saved changes to “{book.title}”.', 'success')
        return redirect(url_for('books.index'))
    return render_template('books/form.html', form=form, book=book)


@bp.post('/<int:book_id>/delete')
def delete(book_id):
    book = db.get_or_404(Book, book_id)
    if book.loans:
        flash(f'“{book.title}” can’t be deleted while copies are out on loan. Return them first.', 'error')
    else:
        title = book.title
        db.session.delete(book)
        db.session.commit()
        flash(f'Deleted “{title}”.', 'success')
    return redirect(url_for('books.index'))


def _fetch_from_frappe(title, pages):
    """Ask the Frappe library API for books matching a title, 20 per page."""
    found = []
    for page in range(1, pages + 1):
        response = requests.get(current_app.config['FRAPPE_API_URL'],
                                params={'page': page, 'title': title}, timeout=10)
        response.raise_for_status()
        batch = response.json().get('message') or []
        if not isinstance(batch, list) or not batch:
            break
        found.extend(batch)
    return found


@bp.route('/import', methods=['GET', 'POST'])
def import_books():
    form = ImportForm()
    if not form.validate_on_submit():
        return render_template('books/import.html', form=form)

    try:
        found = _fetch_from_frappe(form.title.data, form.pages.data)
    except (requests.RequestException, ValueError):
        flash('Couldn’t reach the Frappe library. Check your connection and try again.', 'error')
        return render_template('books/import.html', form=form)

    if not found:
        flash(f'Frappe has no books matching “{form.title.data}”.', 'warning')
        return render_template('books/import.html', form=form)

    # A book counts as a duplicate when the same title and author are already in the catalog,
    # including books added earlier in this same import.
    known = {(title.lower(), author.lower())
             for title, author in db.session.execute(select(Book.title, Book.author))}
    added = skipped = 0
    for item in found:
        title = (item.get('title') or '').strip()
        author = (item.get('authors') or 'Unknown').strip()
        if not title or (title.lower(), author.lower()) in known:
            skipped += 1
            continue
        known.add((title.lower(), author.lower()))
        copies = current_app.config['DEFAULT_STOCK']
        db.session.add(Book(title=title, author=author,
                            isbn=str(item.get('isbn') or item.get('isbn13') or '').strip(),
                            stock=copies, borrow_stock=copies))
        added += 1
    db.session.commit()

    if added:
        message = f'Imported {added} {"book" if added == 1 else "books"}.'
        if skipped:
            message += f' Skipped {skipped} already in the catalog.'
        flash(message, 'success')
        return redirect(url_for('books.index'))

    flash(f'All {skipped} matching books are already in the catalog.', 'warning')
    return render_template('books/import.html', form=form)
