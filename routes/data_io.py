import csv
import io
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from models import db, Contact, Category
from utils.validators import validate_email_format, validate_phone_format, check_contact_duplicates

data_io_bp = Blueprint('data_io', __name__)

CSV_HEADERS = [
    'first_name', 'last_name', 'phone', 'alternate_phone', 'email',
    'company', 'job_title', 'address', 'city', 'birthday', 'category', 'notes'
]


@data_io_bp.route('/contacts/export')
@login_required
def export_contacts():
    """Exports all contacts of the current user to a downloadable CSV file."""
    contacts = Contact.query.filter_by(user_id=current_user.id).order_by(Contact.first_name.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

    # Write header
    writer.writerow([
        'First Name', 'Last Name', 'Phone', 'Alternate Phone', 'Email',
        'Company', 'Job Title', 'Address', 'City', 'Birthday',
        'Category', 'Notes', 'Favorite', 'Created At'
    ])

    for c in contacts:
        writer.writerow([
            c.first_name,
            c.last_name or '',
            c.phone or '',
            c.alternate_phone or '',
            c.email or '',
            c.company or '',
            c.job_title or '',
            c.address or '',
            c.city or '',
            c.birthday.strftime('%Y-%m-%d') if c.birthday else '',
            c.category_rel.name if c.category_rel else '',
            c.notes or '',
            'Yes' if c.is_favorite else 'No',
            c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    filename = f"contacts_export_{today_str}.csv"

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@data_io_bp.route('/contacts/sample-csv')
@login_required
def download_sample_csv():
    """Provides a sample CSV template for users to format their contacts."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(CSV_HEADERS)
    writer.writerow([
        'Sarah', 'Connor', '+1 (555) 234-5678', '+1 (555) 876-5432', 'sarah.connor@cyberdyne.io',
        'Cyberdyne Systems', 'Chief Security Officer', '100 Tech Blvd', 'San Francisco', '1985-05-12', 'Work', 'Key executive contact'
    ])
    writer.writerow([
        'Michael', 'Scott', '555-123-4567', '', 'michael.scott@dundermifflin.com',
        'Dunder Mifflin', 'Regional Manager', '1725 Slough Avenue', 'Scranton', '1965-03-15', 'Clients', "World's Best Boss"
    ])
    writer.writerow([
        'Emily', 'Watson', '+44 20 7946 0912', '', 'emily.watson@oxford.edu',
        'University of Oxford', 'Research Scholar', 'High Street', 'Oxford', '1992-11-28', 'University', 'Met at AI conference'
    ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename="contacts_template.csv"'}
    )


@data_io_bp.route('/contacts/import', methods=['GET', 'POST'])
@login_required
def import_contacts():
    """Handles uploading and parsing of a contact CSV file with duplicate and error handling."""
    if request.method == 'POST':
        if 'csv_file' not in request.files:
            flash('No file selected. Please choose a CSV file to upload.', 'warning')
            return redirect(request.url)

        file = request.files['csv_file']
        if not file or not file.filename:
            flash('No file selected.', 'warning')
            return redirect(request.url)

        if not file.filename.lower().endswith('.csv'):
            flash('Unable to import this file. Please upload a valid .csv file.', 'danger')
            return redirect(request.url)

        try:
            # Read file stream with encoding fallback
            file_bytes = file.read()
            try:
                content = file_bytes.decode('utf-8-sig')
            except UnicodeDecodeError:
                content = file_bytes.decode('latin-1')

            csv_file = io.StringIO(content)
            reader = csv.DictReader(csv_file)

            if not reader.fieldnames:
                flash('The uploaded CSV file is empty or missing headers.', 'danger')
                return redirect(request.url)

            # Normalize fieldnames: lowercase and strip
            field_map = {name.strip().lower().replace(' ', '_'): name for name in reader.fieldnames}

            # Helper to get value from row flexibly
            def get_val(row, *aliases):
                for alias in aliases:
                    if alias in field_map:
                        orig = field_map[alias]
                        if orig in row and row[orig]:
                            return row[orig].strip()
                return ''

            imported_count = 0
            duplicate_count = 0
            invalid_count = 0
            error_details = []

            # Cache user categories to prevent repeated queries
            user_categories = {cat.name.lower(): cat for cat in Category.query.filter_by(user_id=current_user.id).all()}

            row_num = 1
            for row in reader:
                row_num += 1
                first_name = get_val(row, 'first_name', 'firstname', 'first')
                last_name = get_val(row, 'last_name', 'lastname', 'last')
                phone = get_val(row, 'phone', 'primary_phone', 'mobile', 'telephone')
                alt_phone = get_val(row, 'alternate_phone', 'alt_phone', 'secondary_phone', 'work_phone')
                email = get_val(row, 'email', 'email_address', 'mail')
                company = get_val(row, 'company', 'organization')
                job_title = get_val(row, 'job_title', 'title', 'position')
                address = get_val(row, 'address', 'street')
                city = get_val(row, 'city')
                birthday_raw = get_val(row, 'birthday', 'dob', 'birth_date')
                category_name = get_val(row, 'category', 'group')
                notes = get_val(row, 'notes', 'note', 'description')

                # Validation: must have first name and at least one contact method
                if not first_name:
                    invalid_count += 1
                    error_details.append(f"Row {row_num}: Skipped (Missing first name)")
                    continue

                if not phone and not email:
                    invalid_count += 1
                    error_details.append(f"Row {row_num} ({first_name}): Skipped (No phone number or email provided)")
                    continue

                if email and not validate_email_format(email):
                    invalid_count += 1
                    error_details.append(f"Row {row_num} ({first_name}): Skipped (Invalid email format '{email}')")
                    continue

                # Check duplicate within user contacts
                duplicates = check_contact_duplicates(
                    user_id=current_user.id,
                    phone=phone if phone else None,
                    email=email if email else None
                )
                if duplicates:
                    duplicate_count += 1
                    error_details.append(f"Row {row_num} ({first_name}): Duplicate skipped ({duplicates[0]})")
                    continue

                # Parse birthday if present
                birthday = None
                if birthday_raw:
                    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d'):
                        try:
                            birthday = datetime.strptime(birthday_raw, fmt).date()
                            break
                        except ValueError:
                            pass

                # Resolve category
                cat_id = None
                if category_name:
                    cat_key = category_name.lower()
                    if cat_key in user_categories:
                        cat_id = user_categories[cat_key].id
                    else:
                        # Auto-create category for user
                        new_cat = Category(user_id=current_user.id, name=category_name.capitalize())
                        db.session.add(new_cat)
                        db.session.flush()
                        user_categories[cat_key] = new_cat
                        cat_id = new_cat.id

                # Create Contact
                contact = Contact(
                    user_id=current_user.id,
                    first_name=first_name,
                    last_name=last_name or None,
                    phone=phone or None,
                    alternate_phone=alt_phone or None,
                    email=email.lower() if email else None,
                    company=company or None,
                    job_title=job_title or None,
                    address=address or None,
                    city=city or None,
                    birthday=birthday,
                    category_id=cat_id,
                    notes=notes or None,
                    is_favorite=False
                )
                db.session.add(contact)
                imported_count += 1

            db.session.commit()

            summary_msg = f"{imported_count} contacts imported, {duplicate_count} duplicates skipped, {invalid_count} invalid rows skipped."
            
            if imported_count > 0:
                flash(summary_msg, 'success')
            else:
                flash(summary_msg, 'warning')

            return render_template(
                'contacts/import_contacts.html',
                summary=summary_msg,
                imported=imported_count,
                duplicates=duplicate_count,
                invalid=invalid_count,
                error_details=error_details
            )

        except Exception as e:
            db.session.rollback()
            flash(f"Unable to import this CSV file: {str(e)}", 'danger')
            return redirect(request.url)

    return render_template('contacts/import_contacts.html')
