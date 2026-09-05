from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Contact, Category
from utils.validators import check_contact_duplicates

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/check-duplicate')
@login_required
def check_duplicate():
    """Real-time duplicate detector endpoint for interactive form feedback."""
    phone = request.args.get('phone', '').strip()
    email = request.args.get('email', '').strip()
    exclude_id = request.args.get('exclude_id')

    exclude_contact_id = int(exclude_id) if exclude_id and exclude_id.isdigit() else None

    warnings = check_contact_duplicates(
        user_id=current_user.id,
        phone=phone if phone else None,
        email=email if email else None,
        exclude_contact_id=exclude_contact_id
    )

    return jsonify({
        'has_duplicate': len(warnings) > 0,
        'warnings': warnings
    })


@api_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def manage_categories():
    """List or create custom categories for current user."""
    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name', '').strip()

        if not name:
            return jsonify({'success': False, 'message': 'Category name cannot be empty.'}), 400

        # Check existing
        existing = Category.query.filter_by(user_id=current_user.id, name=name).first()
        if existing:
            return jsonify({'success': False, 'message': 'This category already exists.', 'id': existing.id}), 409

        new_cat = Category(user_id=current_user.id, name=name)
        db.session.add(new_cat)
        db.session.commit()

        return jsonify({'success': True, 'id': new_cat.id, 'name': new_cat.name}), 201

    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.name.asc()).all()
    return jsonify([{'id': c.id, 'name': c.name} for c in categories])


@api_bp.route('/stats')
@login_required
def get_stats():
    """Fetches real-time dashboard analytics for charts."""
    categories = Category.query.filter_by(user_id=current_user.id).all()
    category_data = []

    for cat in categories:
        count = Contact.query.filter_by(user_id=current_user.id, category_id=cat.id).count()
        if count > 0:
            category_data.append({'category': cat.name, 'count': count})

    uncategorized = Contact.query.filter_by(user_id=current_user.id, category_id=None).count()
    if uncategorized > 0:
        category_data.append({'category': 'Uncategorized', 'count': uncategorized})

    return jsonify({
        'total': Contact.query.filter_by(user_id=current_user.id).count(),
        'favorites': Contact.query.filter_by(user_id=current_user.id, is_favorite=True).count(),
        'categories': category_data
    })

