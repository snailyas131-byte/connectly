# Connectly &mdash; Smart Contact Management Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**Connectly** is a secure, modern, multi-user full-stack contact management web application and lightweight CRM built to organize, search, and manage personal and professional contacts seamlessly. Designed with a sleek responsive UI/UX and native Dark/Light mode, Connectly ensures that every user's contacts remain private and isolated while providing advanced productivity features such as duplicate detection, bulk CSV import/export, and interactive contact analytics.

---

## 📸 Screenshots

> Screenshots are located in [`docs/screenshots/`](docs/screenshots/).

| View | Description |
|---|---|
| **Dashboard** | Overview of contacts, statistics cards, and category breakdown chart |
| **Add / Edit Contact** | Intuitive contact form with live avatar preview & duplicate detection |
| **Contact Details** | Complete profile page with quick call/email actions and notes |
| **Search & Filters** | Real-time multi-field search, category tabs, and sorting options |
| **CSV Importer** | Bulk import contacts with error tolerance and duplicate skipping |
| **Dark Mode** | Eye-friendly dark theme with persistent theme preference |

---

## ✨ Features

- **User Registration & Authentication**: Secure sign-up and sign-in with "Remember Me" powered by Flask-Login.
- **Password Hashing**: Industry-standard password hashing using Werkzeug Security.
- **Multi-User Contact Isolation**: Strict database scoping ensures a logged-in user can never view or modify another user's contacts.
- **Add, View, Edit & Delete Contacts**: Full CRUD capabilities with support for phone numbers, email, company, job title, physical address, birthday, and rich notes.
- **Confirmation Dialogs**: Protection against accidental deletions with clear modal dialogs.
- **Contact Categories**: Organize contacts by *Family, Friends, Work, Clients, University, Other*, or custom user-defined categories.
- **Favorite Contacts**: Quick star/unstar toggle with asynchronous AJAX updates.
- **Profile Picture Uploads**: Upload profile photos (PNG, JPG, JPEG, WEBP) stored securely with randomized UUID filenames and automatic cleanup.
- **Duplicate Detection**: Real-time inline warnings and backend validation to detect and prevent duplicate phone numbers or email addresses.
- **Real-Time Search**: Instant case-insensitive filtering across names, phones, emails, companies, titles, categories, and cities.
- **Sorting & Filtering**: Sort by Name (A-Z, Z-A), Newest, Oldest, or Recently Updated, combined with category filters.
- **CSV Import with Summary Report**: Bulk upload contacts with malformed-row tolerance, duplicate skipping, and detailed logs.
- **CSV Export**: One-click download of your personal contact directory into a standard CSV file.
- **Contact Statistics & Analytics**: Live summary cards and an interactive category distribution doughnut chart powered by Chart.js.
- **Recently Added Contacts**: Quick access to your 5 most recent contacts in the dashboard sidebar.
- **Dark / Light Mode**: Full theme customization with instant toggle and `localStorage` persistence.
- **Responsive Design**: Fluid layout tailored for mobile, tablet, laptop, and desktop viewports.
- **Flash Notifications**: User-friendly alerts for success, warnings, and error messages.
- **Custom Error Pages**: Styled custom pages for 403 Forbidden, 404 Not Found, 413 File Too Large, and 500 Server Error.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug, Pillow, email-validator, python-dotenv
- **Database**: SQLite, SQLAlchemy ORM
- **Frontend**: HTML5, CSS3 (Modern CSS Custom Properties & Grid/Flexbox), JavaScript (ES6+), Jinja2
- **UI Components & Visuals**: FontAwesome 6, Chart.js 4
- **Testing**: Python `unittest`

---

## 📁 Project Structure

```
connectly/
├── app.py                     # Application factory, blueprint registration & error handlers
├── config.py                  # Configuration settings & upload limits
├── models.py                  # Database schema (User, Category, Contact)
├── run.bat                    # One-click Windows launcher
├── requirements.txt           # Python package dependencies
├── .env.example               # Safe environment variable template
├── .gitignore                 # Git ignore configuration
├── README.md                  # Project documentation
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                # User registration, login, logout
│   ├── contacts.py            # Contact CRUD, dashboard, search & filtering
│   ├── data_io.py             # CSV export, CSV import & template generator
│   └── api.py                 # AJAX duplicate detection, stats & categories
│
├── utils/
│   ├── __init__.py
│   ├── validators.py          # Data validation & duplicate detection logic
│   └── file_handler.py        # Safe avatar upload & deletion utilities
│
├── static/
│   ├── css/
│   │   └── style.css          # Design system & dark/light mode styles
│   ├── js/
│   │   └── main.js            # Live search, theme switcher, AJAX favorites & modals
│   ├── images/
│   │   └── default-avatar.svg # Default avatar graphic
│   └── uploads/
│       └── avatars/           # Contact profile pictures (.gitkeep)
│
├── templates/
│   ├── base.html              # Base layout with navbar & alerts
│   ├── index.html             # Guest landing page
│   ├── dashboard.html         # Main dashboard with contacts grid & charts
│   ├── auth/
│   │   ├── login.html         # Login page
│   │   └── register.html      # Registration page
│   ├── contacts/
│   │   ├── add_contact.html   # Add contact form
│   │   ├── edit_contact.html  # Edit contact form
│   │   ├── contact_details.html # Contact profile view
│   │   └── import_contacts.html # CSV import dropzone & instructions
│   └── errors/
│       ├── 403.html           # 403 Forbidden page
│       ├── 404.html           # 404 Not Found page
│       ├── 413.html           # 413 File Too Large page
│       └── 500.html           # 500 Internal Server Error page
│
├── docs/
│   └── screenshots/           # Application screenshots (.gitkeep)
│
├── sample_data/
│   └── contacts_sample.csv    # Sample CSV for testing import
│
└── tests/
    ├── __init__.py
    └── test_app.py            # Automated unit and integration tests
```

---

## 🚀 Installation & Setup

### Option 1: One-Click Launcher (Windows)
Double-click **`run.bat`** in the project folder. It will automatically initialize the virtual environment, install dependencies, launch the server, and open the application in your default browser.

---

### Option 2: Manual Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/snailyas131-byte/connectly.git
cd connectly
```

#### 2. Create and Activate a Virtual Environment

**On Windows (PowerShell / Command Prompt):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Environment Configuration (Optional)
Copy the example environment file:
```bash
cp .env.example .env
```

#### 5. Database Initialization
Database tables are automatically created on first startup using SQLite. No manual migration commands are required.

#### 6. Run the Application
```bash
python app.py
```

#### 7. Access in Browser
Open:
```
http://127.0.0.1:5000/
```

---

## 🧪 Automated Testing

Connectly includes a comprehensive test suite covering authentication, CRUD, multi-user isolation, CSV processing, and duplicate detection:

```bash
python -m unittest discover -s tests -v
```

---

## 📋 CSV Import Format

When importing contacts from CSV, your file should include a header row with supported column names:

| Header | Required | Example |
|---|---|---|
| `first_name` | **Yes** | Sarah |
| `last_name` | No | Connor |
| `phone` | *At least 1 method* | +1 (555) 234-5678 |
| `email` | *At least 1 method* | sarah@cyberdyne.io |
| `alternate_phone` | No | +1 (555) 876-5432 |
| `company` | No | Cyberdyne Systems |
| `job_title` | No | Chief Security Officer |
| `address` | No | 100 Tech Blvd |
| `city` | No | San Francisco |
| `birthday` | No | 1985-05-12 |
| `category` | No | Work |
| `notes` | No | Key executive contact |

---

## 🔒 Security Practices

- **Password Hashing**: Werkzeug's secure hashing algorithm protects stored credentials.
- **Route Authorization**: Flask-Login protects all authenticated endpoints against unauthorized access.
- **User Ownership Verification**: Every query filters by `user_id == current_user.id`, preventing cross-tenant access.
- **Safe File Uploads**: Uploaded files undergo MIME type verification, extension whitelisting, file size restrictions (5MB limit), and unique randomized UUID filenames.
- **SQL Injection Prevention**: SQLAlchemy ORM ensures all parameterized queries.
- **Cross-Site Scripting (XSS) Protection**: Jinja2 automatic escaping prevents malicious script injection.

---

## 🔮 Future Improvements

- [ ] Two-Factor Authentication (2FA) via Authenticator apps
- [ ] vCard (.vcf) format import and export
- [ ] Email notifications & birthday reminders
- [ ] Multi-tag labeling for contacts
- [ ] Cloud-based profile image storage (AWS S3 / Cloudinary)

---

## 👩‍💻 Author

**Sana Ilyas**  
GitHub: [@snailyas131-byte](https://github.com/snailyas131-byte)

---

## 📄 License

This project is licensed under the MIT License.
