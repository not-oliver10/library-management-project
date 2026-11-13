# What changed

## Bugs fixed

- `app.py` compared `__name__` to `'main'`, so `python app.py` never started the server. It now checks `'__main__'`.
- The development `SECRET_KEY` was an empty string, which makes Flask-WTF fail on every form. Settings now come from environment variables, with a working development default, and the app refuses to start in production without a real key.
- Heroku's `postgres://` database URL is converted to `postgresql://`, which SQLAlchemy requires. `DATABASE_URL` is read as well as `SQL_DATABASE_URL`.
- Choosing the placeholder option ("Members", "Books to return") crashed the borrow and return routes with a 500 error. Selects are now validated and show a clear message.
- Redirects used `request.referrer`, which can be empty and crashed the route. Redirects now go to fixed pages.
- Editing a book added the entered number to `stock` on every save (the old code compared strings with `is not`, which is always true) and overwrote the count of copies on the shelf. Editing now sets the total number of copies and works out the shelf count from the loans that are out. It refuses a total lower than the number on loan.
- Returning a book never checked that the member had borrowed it, so stock could be inflated. Returns are now done by choosing an actual loan.
- If a member borrowed the same book twice, returning it removed both loan rows but gave back one copy. A member can no longer hold two copies of the same title.
- The borrow and return rules were only enforced by hiding options in the dropdown. The server now checks stock and the debt limit itself.
- Members at the debt limit could never pay it off, because there was no way to record a payment. There is now a "Record payment" action.
- Returning with "paid" ticked could push a member's balance below zero. It now only takes what they owe.
- A book with 0 copies couldn't be created, because `DataRequired` rejects 0.
- Form errors were shown as raw Python lists, such as `['Book already exists']`. They now appear next to the field.
- Importing from Frappe skipped any book whose author was already in the catalog, even with a different title. It now skips only the same title and author. It also URL-encodes the search, has a timeout, handles API errors, and saves everything in one commit.
- Deleting a book or member that has books out failed with a generic error. It now explains why.
- Updating a book or member skipped validation completely, so duplicate usernames and phone numbers could slip through.
- Deleting used GET as well as POST, so a link could delete data. Destructive actions are POST only.
- There was no CSRF protection on update, delete, borrow or return. It is now on for every form.
- The return dropdown script threw an error on pages without the return form, appended duplicate members every time the book changed, and inserted member names as raw HTML (a cross-site scripting risk). That script is gone.
- Chart.js was loaded twice, in two versions, on every page.
- Every row on the Books page included its own copy of the borrow modal with every book and member in it, so the page grew with the square of the catalog. Pages are now paginated and there is nothing repeated per row.
- `Book.query.filter(Book.borrower)` and string `order_by('id')` are replaced with proper queries.
- Search was a POST form, so refreshing re-submitted it and results couldn't be bookmarked. It is now a GET with a URL.
- The tests wrapped imports in `try/except`, compared bytes to a string, and needed a live PostgreSQL database with specific rows in it. They are rewritten to use an in-memory database.
- `psycopg2` needed a C compiler to install, and `requirements.txt` listed about 25 packages the app doesn't use (including `discord.py`) on 2021 versions. It is now nine packages.

## Improvements

- Redesigned interface: one desk page for issuing and returning, spine-colour tabs and availability meters on books, a ledger for transactions, and ranked bars for reports. It works on phones, has visible keyboard focus and uses no Bootstrap, no jQuery and no charting library, so there is nothing to load from a CDN except the two fonts, which have fallbacks.
- Pagination and search on books, members and transactions.
- Add and edit pages with inline validation, instead of pop-ups that closed on errors.
- Library rules (fee, debt limit, default stock, currency) are settings, not numbers buried in the code.
- Friendly 404, 405 and 500 pages.
- `flask seed-demo` and `flask init-db` commands.
- The app is built by a `create_app()` factory, with the issue, return and payment rules in `library/services.py`.

## Database

The database schema is unchanged, so existing data keeps working. Books that were edited under the old code may have an inflated `stock` value. Open each one with Edit and set the correct total number of copies.
