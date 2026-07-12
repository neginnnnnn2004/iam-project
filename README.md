# 🛡️ DomainAuth - Identity & Access Management (IAM) Service

`DomainAuth` is a centralized, production-ready **Identity & Access Management (IAM)** web service built with **Django** and **Django REST Framework (DRF)**.

Designed with a highly clean, decoupled architecture, this service manages custom user authentication, granular group permissions, and enterprise domain tracking with dynamic tagging. It features a completely stateless, time-sensitive password reset mechanism that ensures top-tier security without database overhead.

---

## 🌟 Key Features

* **Custom User Architecture:** Built using a customized Django User Model (`CustomUser`), allowing seamless scalability for enterprise-level user fields.
* **Granular Access Control:** Comprehensive management of user authentication, groups, and system permissions.
* **Stateless Password Reset:** Generates secure, cryptographic, time-sensitive tokens via Django's `TimestampSigner`. Tokens expire automatically after 10 minutes without requiring database storage.
* **User Enumeration Protection:** The password reset request endpoint returns a generic, ambiguous success message regardless of whether the username exists, preventing malicious actors from mapping active users.
* **Domain & Tag Management:** Allows registration of organizational domains coupled with dynamic tagging, facilitating smart classification, filtering, and multi-tenant domain mapping.
* **Automated Testing:** Robust, module-based test coverage ensuring each core service component functions reliably.

---

## 📁 Project Architecture & Structure

The project strictly follows the **Separation of Concerns (SoC)** principle, breaking down views, serializers, and test suites into domain-specific modules for maximum maintainability:

```text
📁 iam2/                      # Project root configuration directory
├── 📁 .idea/                 # IDE configurations
├── 📁 .venv/                 # Python Virtual Environment
├── 📁 accounts/              # Main IAM and user management application
│   ├── 📁 migrations/        # Database migration files (Initial to domain/group updates)
│   ├── 📁 serializers/       # Decoupled DRF serializers matching each module
│   │   ├── __init__.py
│   │   ├── auth_serializers.py
│   │   ├── domain_serializers.py
│   │   ├── group_serializers.py
│   │   └── user_serializers.py
│   ├── 📁 tests/             # Dedicated unit and integration test suites
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_domain.py
│   │   ├── test_group.py
│   │   └── test_user.py
│   ├── 📁 views/             # Decoupled views handling distinct operations
│   │   ├── __init__.py
│   │   ├── auth_views.py
│   │   ├── domain_views.py
│   │   ├── group_views.py
│   │   ├── reset_pass_views.py
│   │   └── user_views.py
│   ├── admin.py              # Admin panel registrations
│   ├── apps.py               # Application configuration
│   ├── models.py             # Custom User and Domain model configurations
│   ├── permissions.py        # Custom API permission classes
│   ├── urls.py               # Local application routing
│   └── utils.py              # Cryptographic token utilities and helpers
├── 📁 iam2/                  # Core Django project configuration folder
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py           # Centralized settings and credentials configuration
│   ├── urls.py               # Global root routing configuration
│   └── wsgi.py
├── .env                      # Local environment variables
├── .env.example              # Sample template for environment configurations
├── .gitignore                # Git ignore configurations
├── LICENSE                   # Project license file
├── manage.py                 # Django command-line utility
└── README.md                 # Project documentation
```

## 🚀 Installation & Setup

Follow these steps to set up and run the service locally:

### 1. Clone the Repository
```bash
git clone [https://github.com/neginnnnnn2004/iam-project.git](https://github.com/neginnnnnn2004/iam-project.git)
cd iam-project
```

## 2. Configure Environment Variables
cp .env.example .env

## 3. Configure Virtual Environment
# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

## 4. Install Dependencies
pip install -r requirements.txt

## 5. Database Migrations
python manage.py migrate

## 6. Run the Test Suite
python manage.py test

## 7. Run the Server
python manage.py runserver

🗺️ API Endpoints Reference
1. Authentication & Profile Management (auth_views.py)
POST /api/accounts/register/ - Registers a new user account profile (Validation codes: 10, 11, 12).

POST /api/accounts/login/ - Authenticates user credentials and issues secure access/refresh JWT tokens.

PUT /api/accounts/profile/ - Full profile schema updates (Requires active JWT token).

PATCH /api/accounts/profile/ - Partial field updates for the current authenticated profile.

2. User Lifecycle & Role Administration (user_views.py)
GET /api/accounts/users/ - Fetches a list of all registered users across the platform.

GET /api/accounts/users/pending/ - Filters and lists all accounts awaiting activation (status="pending"). Requires Admin privileges.

GET /api/accounts/roles/ - Lists all available system assignment roles.

PATCH /api/accounts/users/<int:pk>/role/ - Assigns a specialized access role to a chosen user (Validation codes: 10, 40).

PATCH /api/accounts/users/<int:pk>/status/ - Modifies a profile's operational state matrix (Validation codes: 10, 40).

DELETE /api/accounts/users/<int:pk>/ - Gracefully updates a target profile to the deleted state and stamps execution time.

PATCH /api/accounts/users/<int:pk>/activation/ - Directly alters the primitive is_active boolean value flags.

3. Stateless Password Reset Flow (reset_pass_views.py)
POST /api/accounts/reset-password/ - Initiates the reset. Sends a secure 10-minute token to the user's registered email (Protected against user enumeration).

POST /api/accounts/reset-password/confirm/ - Validates the cryptographic token and securely hashes/saves the new password.

4. Enterprise Domain & Tag Management (domain_views.py)
POST /api/accounts/domains/import/ - Admin-only operation to import or create structured domains.

GET /api/accounts/domains/ - Retrieves a tailored list of active domains depending on group visibility or admin scopes.

POST /api/accounts/tags/ - Creates a tracking metadata tag in the system (Admin-only).

GET /api/accounts/tags/ - Returns a dictionary list of all valid registered tracking metadata tags.

POST /api/accounts/domains/assign-tag/ - Bulk records assignment of metadata tags to specified domains (Handles conflict monitoring).

PATCH /api/accounts/domains/assign-tag/ - Multi-record transaction patch updating domain tags with explicit verification confirm flags.

5. Group & Access Control Management (group_views.py)
GET /api/accounts/groups/ - Lists all available operational organizational groups (Admin-only).

POST /api/accounts/groups/ - Instantiates a new system access or organizational group profile.

GET /api/accounts/groups/<int:pk>/ - Fetches detailed single-group structural metadata (Includes soft-delete filtration).

PUT /api/accounts/groups/<int:pk>/ - Completely updates group properties and operational identifiers.

PATCH /api/accounts/groups/<int:pk>/ - Selectively alters single properties on an active group profile.

DELETE /api/accounts/groups/<int:pk>/ - Handles graceful soft-deletion of organizational groups using timestamp tracking.

POST /api/accounts/groups/assign-user/ - Bridges active users to organizational access groups.

🛠️ Tech Stack & Security Implementations
Core Framework: Django

API Delivery & Documentation: Django REST Framework (DRF) & drf-yasg (Swagger/OpenAPI UI integration)

Token Operations: djangorestframework-simplejwt (JSON Web Tokens)

Cryptographic Signing: Django Core Signers (TimestampSigner)

Security Practices: Password hashing (PBKDF2), atomic transaction blocks for bulk tasks (transaction.atomic), custom protection filters against user enumeration attacks, and timing-attack resilient user lookups.