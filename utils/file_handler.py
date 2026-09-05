import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app


def allowed_file(filename: str) -> bool:
    """Check if the uploaded file has an allowed image extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_IMAGE_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp', 'gif'})


def save_profile_picture(file) -> str | None:
    """
    Saves an uploaded image file with a unique secure filename in the upload folder.
    Returns the generated filename or None if saving failed or file is invalid.
    """
    if not file or not file.filename:
        return None

    if not allowed_file(file.filename):
        return None

    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"avatar_{uuid.uuid4().hex[:12]}_{int(uuid.uuid1().time_low)}.{ext}"
    
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)

    return unique_filename


def delete_profile_picture(filename: str | None) -> bool:
    """Deletes a profile picture from disk if it exists and is not default."""
    if not filename:
        return False
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER')
    if not upload_folder:
        return False

    file_path = os.path.join(upload_folder, filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.remove(file_path)
            return True
        except OSError:
            return False
    return False

