from library import db
from library.models import Book, Member

BOOKS = [
    ('The Left Hand of Darkness', 'Ursula K. Le Guin', '9780441478125', 4),
    ('Pride and Prejudice', 'Jane Austen', '9780141439518', 6),
    ('One Hundred Years of Solitude', 'Gabriel García Márquez', '9780060883287', 3),
    ('The Remains of the Day', 'Kazuo Ishiguro', '9780679731726', 2),
    ('Midnight’s Children', 'Salman Rushdie', '9780812976533', 3),
    ('Things Fall Apart', 'Chinua Achebe', '9780385474542', 5),
    ('Cairo Modern', 'Naguib Mahfouz', '9780385264662', 2),
    ('The Name of the Rose', 'Umberto Eco', '9780544176560', 3),
]

MEMBERS = [
    ('Amira Hassan', 'amira', '0100 555 0101'),
    ('Omar Farouk', 'omarf', '0100 555 0102'),
    ('Lena Schmidt', 'lena', '0100 555 0103'),
    ('Karim Nabil', 'karim', '0100 555 0104'),
]


def seed():
    """Add demo data to an empty database. Returns False if there was already data."""
    if Book.query.first() or Member.query.first():
        return False
    for title, author, isbn, copies in BOOKS:
        db.session.add(Book(title=title, author=author, isbn=isbn, stock=copies, borrow_stock=copies))
    for name, username, phone in MEMBERS:
        db.session.add(Member(name=name, member_name=username, phone_number=phone))
    db.session.commit()
    return True
