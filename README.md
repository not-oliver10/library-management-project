# Library desk

A library management system built with Flask. Staff keep a catalog of books and a list of members, issue and return books from one desk page, track the fees members owe, and see which books and members stand out.

## Features

- **Circulation desk.** Issue a book to a member, or return one from the list of loans, on a single page. A fee is added each time a book is issued and can be collected when the book comes back.
- **Books.** Add, edit and delete books. See at a glance how many copies are on the shelf. Search by title, author or ISBN.
- **Import from Frappe.** Search the Frappe library API by title and add the results, skipping books you already have.
- **Members.** Add, edit and delete members, search them, and record payments against what they owe. Members who owe too much can't borrow until they pay.
- **Transactions.** A ledger of every issue, return and payment, with filters.
- **Reports.** Most borrowed books and the members who have paid the most.

## Built with

Flask, SQLAlchemy (SQLite locally, PostgreSQL in production), Flask-WTF, and hand-written HTML, CSS and a little JavaScript. There is no front-end build step.

## Run it locally

```bash
git clone <your repository url>
cd <the project folder>
python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt

flask --app app seed-demo       # optional: adds a few books and members to try
flask --app app run --debug
```

Open http://127.0.0.1:5000. The tables are created automatically on first start, and `flask --app app init-db` creates any that are missing. Locally the app uses a SQLite file, `library/library.db`.

## Settings

Settings are read from environment variables, or from a `.env` file (copy `.env.example`).

| Variable | Default | What it does |
| --- | --- | --- |
| `SECRET_KEY` | a development key | Signs sessions and forms. **Required when `DATABASE_URL` is set.** |
| `DATABASE_URL` | local SQLite file | Database to use. `postgres://` URLs are converted for you. |
| `BORROW_FEE` | `30` | Added to a member's balance each time a book is issued. |
| `DEBT_LIMIT` | `500` | Members who owe this much or more can't borrow. |
| `DEFAULT_STOCK` | `20` | Copies created for each imported book. |
| `CURRENCY` | empty | Text shown before amounts, for example `Rs. ` or `$`. |
| `FRAPPE_API_URL` | `https://frappe.io/api/method/frappe-library` | Where imports come from. |

## Deploy to Heroku

```bash
heroku create
heroku addons:create heroku-postgresql
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
git push heroku main
```

Heroku sets `DATABASE_URL` for you, and the `Procfile` starts the app with gunicorn.

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest
```
