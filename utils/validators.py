import re
from datetime import datetime
from models import Contact, User

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_ALLOWED_CHARS = re.compile(r"^[0-9+\-\s()./extEXT#*]+$")


def validate_email_format(email: str) -> bool:
    """Validates email format using regex."""
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_phone_format(phone: str) -> bool:
    """Validates phone number allowing international prefixes, dashes, spaces, parentheses, extensions."""
    if not phone:
        return True
    cleaned = phone.strip()
    if not PHONE_ALLOWED_CHARS.match(cleaned):
        return False
    # Count actual digits
    digits = re.sub(r"\D", "", cleaned)
    return 5 <= len(digits) <= 20



def validate_registration(full_name: str, email: str, password: str, confirm_password: str) -> tuple[bool, str]:
    """Validates user registration form input."""
    if not full_name or len(full_name.strip()) < 2:
        return False, "Please enter your full name (minimum 2 characters)."
    
    if not email or not validate_email_format(email):
        return False, "Please provide a valid email address."
    
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    if password != confirm_password:
        return False, "Passwords do not match."
    
    # Check if email is already taken
    existing_user = User.query.filter_by(email=email.strip().lower()).first()
    if existing_user:
        return False, "An account with this email address already exists."
    
    return True, ""


def check_contact_duplicates(user_id: int, phone: str = None, email: str = None, exclude_contact_id: int = None) -> list[str]:
    """
    Checks if a contact with the same phone or email already exists for the given user.
    Returns a list of warning messages for detected duplicates.
    """
    warnings = []
    
    clean_phone = phone.strip() if phone else ""
    clean_email = email.strip().lower() if email else ""

    if clean_phone:
        query = Contact.query.filter(
            Contact.user_id == user_id,
            (Contact.phone == clean_phone) | (Contact.alternate_phone == clean_phone)
        )
        if exclude_contact_id:
            query = query.filter(Contact.id != exclude_contact_id)
        
        match = query.first()
        if match:
            warnings.append(f"A contact with phone number '{clean_phone}' already exists ({match.full_name}).")

    if clean_email:
        query = Contact.query.filter(
            Contact.user_id == user_id,
            Contact.email.ilike(clean_email)
        )
        if exclude_contact_id:
            query = query.filter(Contact.id != exclude_contact_id)
            
        match = query.first()
        if match:
            warnings.append(f"A contact with email address '{clean_email}' already exists ({match.full_name}).")

    return warnings


def validate_contact_form(data: dict) -> tuple[bool, str]:
    """Validates contact creation/update payload."""
    first_name = data.get('first_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    birthday_str = data.get('birthday', '').strip()

    if not first_name:
        return False, "First name is required."

    if not phone and not email:
        return False, "Please provide at least one contact method (phone or email)."

    if phone and not validate_phone_format(phone):
        return False, "Please enter a valid phone number (digits, optional '+', dashes, parentheses)."

    alternate_phone = data.get('alternate_phone', '').strip()
    if alternate_phone and not validate_phone_format(alternate_phone):
        return False, "Please enter a valid alternate phone number."

    if email and not validate_email_format(email):
        return False, "Please enter a valid email address."

    if birthday_str:
        try:
            datetime.strptime(birthday_str, '%Y-%m-%d')
        except ValueError:
            return False, "Invalid birthday date format. Expected YYYY-MM-DD."

    return True, ""
