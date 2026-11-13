"""Run with:  pip install -r requirements-dev.txt  then  pytest"""
import pytest

from library import create_app, db
from library.models import Book, Loan, Member, Transaction


@pytest.fixture()
def app():
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test',
    })
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def add_book(app, title='Dune', author='Frank Herbert', stock=2):
    with app.app_context():
        book = Book(title=title, author=author, isbn='9780441172719', stock=stock, borrow_stock=stock)
        db.session.add(book)
        db.session.commit()
        return book.id


def add_member(app, username='amira', phone='0100 555 0101', to_pay=0):
    with app.app_context():
        member = Member(name='Amira Hassan', member_name=username, phone_number=phone, to_pay=to_pay)
        db.session.add(member)
        db.session.commit()
        return member.id


def issue(client, book_id, member_id):
    return client.post('/transactions/issue', data={'book_id': book_id, 'member_id': member_id},
                       follow_redirects=True)


def text(response):
    return response.get_data(as_text=True)


def test_every_page_loads(client):
    for url in ('/', '/books/', '/books/new', '/books/import', '/members/', '/members/new',
                '/transactions/', '/reports'):
        assert client.get(url).status_code == 200, url


def test_unknown_page_shows_friendly_404(client):
    response = client.get('/nope')
    assert response.status_code == 404
    assert 'Page not found' in text(response)


def test_create_book(app, client):
    response = client.post('/books/new', data={'title': 'Dune', 'author': 'Frank Herbert',
                                               'isbn': '123', 'stock': '3'}, follow_redirects=True)
    assert 'Added' in text(response)
    with app.app_context():
        book = Book.query.one()
        assert (book.stock, book.borrow_stock) == (3, 3)


def test_zero_copies_is_allowed_and_bad_numbers_are_not(client):
    ok = client.post('/books/new', data={'title': 'A', 'author': 'B', 'isbn': '1', 'stock': '0'},
                     follow_redirects=True)
    assert 'Added' in text(ok)
    bad = client.post('/books/new', data={'title': 'C', 'author': 'D', 'isbn': '1', 'stock': 'abc'})
    assert bad.status_code == 200
    assert 'Added' not in text(bad)


def test_duplicate_book_is_rejected(app, client):
    add_book(app)
    response = client.post('/books/new', data={'title': 'dune', 'author': 'FRANK HERBERT',
                                               'isbn': '1', 'stock': '1'})
    assert 'already in the catalog' in text(response)
    with app.app_context():
        assert Book.query.count() == 1


def test_duplicate_member_username_and_phone_are_rejected(app, client):
    add_member(app)
    response = client.post('/members/new', data={'name': 'Other', 'member_name': 'AMIRA',
                                                 'phone_number': '0100 555 0101'})
    assert 'already uses this username' in text(response)
    assert 'already uses this phone number' in text(response)


def test_issue_and_return_flow(app, client):
    book_id, member_id = add_book(app), add_member(app)

    assert 'Issued' in text(issue(client, book_id, member_id))
    with app.app_context():
        book, member = db.session.get(Book, book_id), db.session.get(Member, member_id)
        assert book.borrow_stock == 1 and book.member_count == 1
        assert member.to_pay == 30
        assert Loan.query.count() == 1
        loan_id = Loan.query.one().id

    response = client.post('/transactions/return', data={'loan_id': loan_id, 'paid': 'on'},
                           follow_redirects=True)
    assert 'was returned' in text(response)
    with app.app_context():
        book, member = db.session.get(Book, book_id), db.session.get(Member, member_id)
        assert book.borrow_stock == 2
        assert (member.to_pay, member.total_paid) == (0, 30)
        assert Loan.query.count() == 0
        kinds = [t.type_of_transaction for t in Transaction.query.order_by(Transaction.id)]
        assert kinds == ['borrow', 'return']


def test_return_without_paying_keeps_the_fee_owed(app, client):
    book_id, member_id = add_book(app), add_member(app)
    issue(client, book_id, member_id)
    with app.app_context():
        loan_id = Loan.query.one().id
    client.post('/transactions/return', data={'loan_id': loan_id})
    with app.app_context():
        assert db.session.get(Member, member_id).to_pay == 30


def test_cannot_issue_when_no_copies_are_left(app, client):
    book_id, member_id = add_book(app, stock=0), add_member(app)
    assert 'No copies' in text(issue(client, book_id, member_id))
    with app.app_context():
        assert Loan.query.count() == 0


def test_member_over_the_debt_limit_cannot_borrow(app, client):
    book_id, member_id = add_book(app), add_member(app, to_pay=500)
    assert 'borrow until they pay' in text(issue(client, book_id, member_id))
    with app.app_context():
        assert Loan.query.count() == 0


def test_same_member_cannot_hold_two_copies_of_one_book(app, client):
    book_id, member_id = add_book(app, stock=3), add_member(app)
    issue(client, book_id, member_id)
    assert 'already has a copy' in text(issue(client, book_id, member_id))
    with app.app_context():
        assert Loan.query.count() == 1


def test_placeholder_choices_do_not_crash(client):
    assert client.post('/transactions/issue', data={'book_id': '', 'member_id': 'Members'},
                       follow_redirects=True).status_code == 200
    assert client.post('/transactions/return', data={'loan_id': 'Books to return'},
                       follow_redirects=True).status_code == 200


def test_books_and_members_with_loans_cannot_be_deleted(app, client):
    book_id, member_id = add_book(app), add_member(app)
    issue(client, book_id, member_id)
    assert 'out on loan' in text(client.post(f'/books/{book_id}/delete', follow_redirects=True))
    assert 'still has books out' in text(client.post(f'/members/{member_id}/delete', follow_redirects=True))
    with app.app_context():
        assert Book.query.count() == 1 and Member.query.count() == 1


def test_deleting_is_post_only(app, client):
    book_id = add_book(app)
    assert client.get(f'/books/{book_id}/delete').status_code == 405


def test_editing_stock_keeps_loans_in_mind(app, client):
    book_id, member_id = add_book(app, stock=3), add_member(app)
    issue(client, book_id, member_id)
    data = {'title': 'Dune', 'author': 'Frank Herbert', 'isbn': '123'}

    client.post(f'/books/{book_id}/edit', data={**data, 'stock': '5'})
    with app.app_context():
        book = db.session.get(Book, book_id)
        assert (book.stock, book.borrow_stock) == (5, 4)

    response = client.post(f'/books/{book_id}/edit', data={**data, 'stock': '0'})
    assert 'out on loan' in text(response)
    with app.app_context():
        assert db.session.get(Book, book_id).stock == 5


def test_record_payment(app, client):
    member_id = add_member(app, to_pay=90)
    client.post(f'/members/{member_id}/pay', data={'amount': '40'})
    with app.app_context():
        member = db.session.get(Member, member_id)
        assert (member.to_pay, member.total_paid) == (50, 40)
        assert Transaction.query.one().type_of_transaction == 'payment'

    too_much = client.post(f'/members/{member_id}/pay', data={'amount': '999'}, follow_redirects=True)
    assert 'only owes' in text(too_much)


def test_search_finds_by_title_author_or_isbn(app, client):
    add_book(app, title='Dune', author='Frank Herbert')
    add_book(app, title='Emma', author='Jane Austen')
    assert 'Frank Herbert' in text(client.get('/books/?q=dun'))
    assert 'Emma' not in text(client.get('/books/?q=dun'))
    assert 'Jane Austen' in text(client.get('/books/?q=austen'))
    assert 'Dune' in text(client.get('/books/?q=9780441172719'))
    assert 'No books match' in text(client.get('/books/?q=%25'))  # % is not a wildcard


def test_import_from_frappe_skips_duplicates(app, client, monkeypatch):
    add_book(app, title='Dune', author='Frank Herbert')

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {'message': [
                {'title': 'Dune', 'authors': 'Frank Herbert', 'isbn': '1'},
                {'title': 'Dune', 'authors': 'Someone Else', 'isbn': '2'},
                {'title': 'Dune Messiah', 'authors': 'Frank Herbert', 'isbn': '3'},
                {'title': 'Dune Messiah', 'authors': 'Frank Herbert', 'isbn': '3'},
            ]}

    monkeypatch.setattr('library.routes.books.requests.get', lambda *a, **k: FakeResponse())
    response = client.post('/books/import', data={'title': 'dune', 'pages': '1'}, follow_redirects=True)
    assert 'Imported 2 books' in text(response)
    with app.app_context():
        assert Book.query.count() == 3


def test_import_reports_api_failure(client, monkeypatch):
    import requests

    def boom(*args, **kwargs):
        raise requests.ConnectionError()

    monkeypatch.setattr('library.routes.books.requests.get', boom)
    response = client.post('/books/import', data={'title': 'dune', 'pages': '1'})
    assert 'reach the Frappe library' in text(response)


def test_heroku_style_database_url_is_fixed(monkeypatch):
    from library.config import _database_url

    monkeypatch.setenv('DATABASE_URL', 'postgres://user:pw@host:5432/db')
    assert _database_url() == 'postgresql://user:pw@host:5432/db'
