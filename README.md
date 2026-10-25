# BuildBack – Final Project

BuildBack is a Flask + SQLite web application for listing, discovering and requesting reusable construction materials.

## 1. Requirements
- Python 3.10 or newer
- VS Code (recommended)

## 2. Open the project
Extract this ZIP. In VS Code choose **File → Open Folder** and select the `BuildBack_Final_Project` folder.

## 3. Create a virtual environment (recommended)
Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If PowerShell blocks activation, run the commands below using `py -m pip` without activating the environment.

## 4. Install packages
```powershell
py -m pip install -r requirements.txt
```

## 5. Initialize the database
```powershell
py database\setup_database.py
```
This creates `database/buildback.db` and the six tables. The Flask app also creates missing tables automatically on startup.

## 6. Run the application
From the main project folder:
```powershell
py app.py
```
Open http://127.0.0.1:5000

The frontend is served by Flask; do not start a separate static server.

## 7. Run tests
```powershell
py -m pytest tests -v
```

## Main features
- User registration and login
- Session-based authentication
- Add, search, update and archive material listings
- Submit and manage material requests
- Create and complete transactions
- Track quantity reused
- Notifications

## Main API endpoints
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health and database check |
| POST | `/api/register` | Register |
| POST | `/api/login` | Login |
| POST | `/api/logout` | Logout |
| GET | `/api/me` | Current user |
| GET/POST | `/api/materials` | List/add materials |
| PUT/DELETE | `/api/materials/<id>` | Update/archive material |
| POST/GET | `/api/requests` | Create/list requests |
| GET | `/api/requests/received` | Incoming requests |
| PUT | `/api/requests/<id>/status` | Accept/reject |
| GET | `/api/transactions` | List transactions |
| PUT | `/api/transactions/<id>/complete` | Complete transaction |
| GET | `/api/impact` | Reuse summary |
| GET | `/api/notifications` | Notifications |

## Important notes
- The app uses a local SQLite database. Do not delete `database/buildback.db` if you want to preserve your data.
- This is a student/demo application. Before public deployment, configure a strong SECRET_KEY, HTTPS, CSRF protection, production server settings and additional security review.
- `schema.sql` documents the six-table database design. `er_diagram.mmd` contains the ER diagram source.
