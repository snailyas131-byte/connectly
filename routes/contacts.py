from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from models import db, Contact, Category
from utils.validators import validate_contact_form, check_contact_duplicates
from utils.file_handler import save_profile_picture, delete_profile_picture

contacts_bp = Blueprint('contacts', __name__)


@contacts_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('contacts.dashboard'))
    return render_template('index.html')


@contacts_bp.route('/dashboard')
@login_required
def dashboard():
    search_query = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    favorites_only = request.args.get('favorites', '').lower() in ['1', 'true', 'yes']
    sort_by = request.args.get('sort', 'name_asc').strip()

    # Base query for logged-in user
    query = Contact.query.filter_by(user_id=current_user.id)

    # Search filter
    if search_query:
        search_pattern = f"%{search_query}%"
        # Join category for searching in category name as well
        query = query.outerjoin(Category, Contact.category_id == Category.id).filter(
            or_(
                Contact.first_name.ilike(search_pattern),
                Contact.last_name.ilike(search_pattern),
                func.concat(Contact.first_name, ' ', func.coalesce(Contact.last_name, '')).ilike(search_pattern),
                Contact.phone.ilike(search_pattern),
                Contact.alternate_phone.ilike(search_pattern),
                Contact.email.ilike(search_pattern),
                Contact.company.ilike(search_pattern),
                Contact.job_title.ilike(search_pattern),
                Contact.city.ilike(search_pattern),
                Category.name.ilike(search_pattern)
            )
        )

    # Category filter
    if category_filter and category_filter != 'all':
        if category_filter.isdigit():
            query = query.filter(Contact.category_id == int(category_filter))
        else:
            query = query.join(Category, Contact.category_id == Category.id).filter(Category.name.ilike(category_filter))

    # Favorites filter
    if favorites_only:
        query = query.filter(Contact.is_favorite == True)

    # Sorting
    if sort_by == 'name_desc':
        query = query.order_by(Contact.first_name.desc(), Contact.last_name.desc())
    elif sort_by == 'newest':
        query = query.order_by(Contact.created_at.desc())
    elif sort_by == 'oldest':
        query = query.order_by(Contact.created_at.asc())
    elif sort_by == 'updated':
        query = query.order_by(Contact.updated_at.desc())
    else:  # name_asc default
        query = query.order_by(Contact.first_name.asc(), Contact.last_name.asc())

    contacts_list = query.all()

    # Statistics
    total_contacts = Contact.query.filter_by(user_id=current_user.id).count()
    favorite_count = Contact.query.filter_by(user_id=current_user.id, is_favorite=True).count()
    
    # Work contacts count
    work_category = Category.query.filter(
        Category.user_id == current_user.id, 
        Category.name.ilike('Work')
    ).first()
    work_count = 0
    if work_category:
        work_count = Contact.query.filter_by(user_id=current_user.id, category_id=work_category.id).count()
    else:
        work_count = Contact.query.filter(
            Contact.user_id == current_user.id,
            (Contact.company.isnot(None) & (Contact.company != ''))
        ).count()

    # Recent contacts (most recent 5)
    recent_contacts = Contact.query.filter_by(user_id=current_user.id)\
        .order_by(Contact.created_at.desc())\
        .limit(5).all()

    # User categories for filter dropdown/tabs
    user_categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()

    # Category breakdown for charts/stats
    category_stats = []
    for cat in user_categories:
        count = Contact.query.filter_by(user_id=current_user.id, category_id=cat.id).count()
        category_stats.append({'name': cat.name, 'count': count})
    
    uncategorized_count = Contact.query.filter_by(user_id=current_user.id, category_id=None).count()
    if uncategorized_count > 0:
        category_stats.append({'name': 'Uncategorized', 'count': uncategorized_count})

    stats = {
        'total': total_contacts,
        'favorites': favorite_count,
        'work': work_count,
        'recent_count': len(recent_contacts),
        'category_stats': category_stats
    }

    return render_template(
        'dashboard.html',
        contacts=contacts_list,
        stats=stats,
        recent_contacts=recent_contacts,
        categories=user_categories,
        search_query=search_query,
        category_filter=category_filter,
        favorites_only=favorites_only,
        sort_by=sort_by
    )


@contacts_bp.route('/contacts/new', methods=['GET', 'POST'])
@login_required
def add_contact():
    user_categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()

    if request.method == 'POST':
        form_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'alternate_phone': request.form.get('alternate_phone', '').strip(),
            'email': request.form.get('email', '').strip().lower(),
            'company': request.form.get('company', '').strip(),
            'job_title': request.form.get('job_title', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'birthday': request.form.get('birthday', '').strip(),
            'category_id': request.form.get('category_id', '').strip(),
            'notes': request.form.get('notes', '').strip(),
            'is_favorite': bool(request.form.get('is_favorite'))
        }

        is_valid, error_msg = validate_contact_form(form_data)
        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('contacts/add_contact.html', form_data=form_data, categories=user_categories)

        # Duplicate checking
        ignore_duplicate = request.form.get('ignore_duplicate') == '1'
        duplicate_warnings = check_contact_duplicates(
            user_id=current_user.id,
            phone=form_data['phone'],
            email=form_data['email']
        )

        if duplicate_warnings and not ignore_duplicate:
            for warning in duplicate_warnings:
                flash(warning, 'warning')
            return render_template(
                'contacts/add_contact.html',
                form_data=form_data,
                categories=user_categories,
                has_duplicate_warning=True,
                duplicate_messages=duplicate_warnings
            )

        # Parse category
        cat_id = None
        if form_data['category_id'] and form_data['category_id'].isdigit():
            # Validate ownership of category
            category = Category.query.filter_by(id=int(form_data['category_id']), user_id=current_user.id).first()
            if category:
                cat_id = category.id

        # Parse birthday
        bday = None
        if form_data['birthday']:
            try:
                bday = datetime.strptime(form_data['birthday'], '%Y-%m-%d').date()
            except ValueError:
                bday = None

        # Handle profile picture upload
        profile_picture = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                profile_picture = save_profile_picture(file)
                if not profile_picture:
                    flash('Invalid image format. Supported formats: JPG, JPEG, PNG, WEBP, GIF (Max 5MB).', 'danger')
                    return render_template('contacts/add_contact.html', form_data=form_data, categories=user_categories)

        # Create contact
        contact = Contact(
            user_id=current_user.id,
            first_name=form_data['first_name'],
            last_name=form_data['last_name'] or None,
            phone=form_data['phone'] or None,
            alternate_phone=form_data['alternate_phone'] or None,
            email=form_data['email'] or None,
            company=form_data['company'] or None,
            job_title=form_data['job_title'] or None,
            address=form_data['address'] or None,
            city=form_data['city'] or None,
            birthday=bday,
            notes=form_data['notes'] or None,
            category_id=cat_id,
            is_favorite=form_data['is_favorite'],
            profile_picture=profile_picture
        )

        db.session.add(contact)
        db.session.commit()

        flash('Contact added successfully.', 'success')
        return redirect(url_for('contacts.view_contact', contact_id=contact.id))

    return render_template('contacts/add_contact.html', categories=user_categories, form_data={})


@contacts_bp.route('/contacts/<int:contact_id>')
@login_required
def view_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()
    return render_template('contacts/contact_details.html', contact=contact)


@contacts_bp.route('/contacts/<int:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()
    user_categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()

    if request.method == 'POST':
        form_data = {
            'first_name': request.form.get('first_name', '').strip(),
            'last_name': request.form.get('last_name', '').strip(),
            'phone': request.form.get('phone', '').strip(),
            'alternate_phone': request.form.get('alternate_phone', '').strip(),
            'email': request.form.get('email', '').strip().lower(),
            'company': request.form.get('company', '').strip(),
            'job_title': request.form.get('job_title', '').strip(),
            'address': request.form.get('address', '').strip(),
            'city': request.form.get('city', '').strip(),
            'birthday': request.form.get('birthday', '').strip(),
            'category_id': request.form.get('category_id', '').strip(),
            'notes': request.form.get('notes', '').strip(),
            'is_favorite': bool(request.form.get('is_favorite'))
        }

        is_valid, error_msg = validate_contact_form(form_data)
        if not is_valid:
            flash(error_msg, 'danger')
            return render_template('contacts/edit_contact.html', contact=contact, form_data=form_data, categories=user_categories)

        # Duplicate check excluding this contact
        ignore_duplicate = request.form.get('ignore_duplicate') == '1'
        duplicate_warnings = check_contact_duplicates(
            user_id=current_user.id,
            phone=form_data['phone'],
            email=form_data['email'],
            exclude_contact_id=contact.id
        )

        if duplicate_warnings and not ignore_duplicate:
            for warning in duplicate_warnings:
                flash(warning, 'warning')
            return render_template(
                'contacts/edit_contact.html',
                contact=contact,
                form_data=form_data,
                categories=user_categories,
                has_duplicate_warning=True,
                duplicate_messages=duplicate_warnings
            )

        # Handle category
        cat_id = None
        if form_data['category_id'] and form_data['category_id'].isdigit():
            category = Category.query.filter_by(id=int(form_data['category_id']), user_id=current_user.id).first()
            if category:
                cat_id = category.id

        # Handle birthday
        bday = None
        if form_data['birthday']:
            try:
                bday = datetime.strptime(form_data['birthday'], '%Y-%m-%d').date()
            except ValueError:
                bday = None

        # Handle avatar remove request
        if request.form.get('remove_picture') == '1':
            if contact.profile_picture:
                delete_profile_picture(contact.profile_picture)
                contact.profile_picture = None

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                new_picture = save_profile_picture(file)
                if new_picture:
                    # Remove previous picture
                    if contact.profile_picture:
                        delete_profile_picture(contact.profile_picture)
                    contact.profile_picture = new_picture
                else:
                    flash('Invalid image format. Supported formats: JPG, JPEG, PNG, WEBP, GIF (Max 5MB).', 'danger')
                    return render_template('contacts/edit_contact.html', contact=contact, form_data=form_data, categories=user_categories)

        # Update contact attributes
        contact.first_name = form_data['first_name']
        contact.last_name = form_data['last_name'] or None
        contact.phone = form_data['phone'] or None
        contact.alternate_phone = form_data['alternate_phone'] or None
        contact.email = form_data['email'] or None
        contact.company = form_data['company'] or None
        contact.job_title = form_data['job_title'] or None
        contact.address = form_data['address'] or None
        contact.city = form_data['city'] or None
        contact.birthday = bday
        contact.category_id = cat_id
        contact.notes = form_data['notes'] or None
        contact.is_favorite = form_data['is_favorite']

        db.session.commit()
        flash('Contact updated successfully.', 'success')
        return redirect(url_for('contacts.view_contact', contact_id=contact.id))

    # Pre-populate form data
    form_data = {
        'first_name': contact.first_name,
        'last_name': contact.last_name or '',
        'phone': contact.phone or '',
        'alternate_phone': contact.alternate_phone or '',
        'email': contact.email or '',
        'company': contact.company or '',
        'job_title': contact.job_title or '',
        'address': contact.address or '',
        'city': contact.city or '',
        'birthday': contact.birthday.strftime('%Y-%m-%d') if contact.birthday else '',
        'category_id': str(contact.category_id or ''),
        'notes': contact.notes or '',
        'is_favorite': contact.is_favorite
    }

    return render_template('contacts/edit_contact.html', contact=contact, form_data=form_data, categories=user_categories)


@contacts_bp.route('/contacts/<int:contact_id>/delete', methods=['POST'])
@login_required
def delete_contact(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()
    
    # Delete profile picture if stored
    if contact.profile_picture:
        delete_profile_picture(contact.profile_picture)

    db.session.delete(contact)
    db.session.commit()

    flash('Contact deleted successfully.', 'success')
    return redirect(url_for('contacts.dashboard'))


@contacts_bp.route('/contacts/<int:contact_id>/toggle-favorite', methods=['POST'])
@login_required
def toggle_favorite(contact_id):
    contact = Contact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()
    contact.is_favorite = not contact.is_favorite
    db.session.commit()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({
            'success': True,
            'is_favorite': contact.is_favorite,
            'message': f"Contact {'marked as' if contact.is_favorite else 'removed from'} favorite."
        })

    flash(f"Contact {'marked as' if contact.is_favorite else 'removed from'} favorite.", 'info')
    return redirect(request.referrer or url_for('contacts.dashboard'))

