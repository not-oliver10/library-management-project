from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import or_, select

from library import db
from library.forms import MemberForm
from library.models import Member
from library.services import LibraryError, record_payment

bp = Blueprint('members', __name__, url_prefix='/members')


def _like_pattern(term):
    escaped = term.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f'%{escaped}%'


@bp.route('/')
def index():
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    stmt = select(Member).order_by(Member.name, Member.id)
    if q:
        pattern = _like_pattern(q)
        stmt = stmt.where(or_(
            Member.name.ilike(pattern, escape='\\'),
            Member.member_name.ilike(pattern, escape='\\'),
            Member.phone_number.ilike(pattern, escape='\\')))

    pagination = db.paginate(stmt, page=page, per_page=current_app.config['PER_PAGE'], error_out=False)
    return render_template('members/index.html', pagination=pagination, q=q)


@bp.route('/new', methods=['GET', 'POST'])
def create():
    form = MemberForm()
    if form.validate_on_submit():
        member = Member(name=form.name.data, member_name=form.member_name.data,
                        phone_number=form.phone_number.data)
        db.session.add(member)
        db.session.commit()
        flash(f'Added {member.name}.', 'success')
        return redirect(url_for('members.index'))
    return render_template('members/form.html', form=form, member=None)


@bp.route('/<int:member_id>/edit', methods=['GET', 'POST'])
def edit(member_id):
    member = db.get_or_404(Member, member_id)
    form = MemberForm(obj=member, member=member)
    if form.validate_on_submit():
        member.name = form.name.data
        member.member_name = form.member_name.data
        member.phone_number = form.phone_number.data
        db.session.commit()
        flash(f'Saved changes to {member.name}.', 'success')
        return redirect(url_for('members.index'))
    return render_template('members/form.html', form=form, member=member)


@bp.post('/<int:member_id>/delete')
def delete(member_id):
    member = db.get_or_404(Member, member_id)
    if member.loans:
        flash(f'{member.name} still has books out. Return them before deleting the member.', 'error')
    else:
        name = member.name
        db.session.delete(member)
        db.session.commit()
        flash(f'Deleted {name}.', 'success')
    return redirect(url_for('members.index'))


@bp.post('/<int:member_id>/pay')
def pay(member_id):
    try:
        amount = request.form.get('amount', type=int)
        member = record_payment(member_id, amount)
        flash(f'Recorded a payment of {amount} from {member.member_name}.', 'success')
    except LibraryError as error:
        flash(str(error), 'error')
    return redirect(url_for('members.index'))
