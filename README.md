# Finance App

A multi-user personal finance web application built with **Flask** and **MySQL**. Users can track expenses, set monthly category budgets, get automated budget advisory feedback, log daily activities, and chat with other users in groups.

## Features

- **Authentication** — secure registration and login with hashed passwords (`werkzeug.security`) and session management via `Flask-Login`.
- **Expense Tracking** — add, view, and delete personal expenses by category, amount, date, and note.
- **Budget Management** — set monthly spending limits per category, with upsert support (create or update in one action).
- **Financial Advisory** — automatically compares monthly spend against budgets and flags categories that are over or under limit.
- **Activity Feed** — a lightweight social feed where users can post updates, shown to all users in reverse chronological order.
- **Group Chat** — create groups, add members by username, and exchange messages within a group (polling-based chat via a JSON API endpoint).
- **Profile Management** — update username and password with current-password verification.

## Tech Stack

- **Backend:** Python, Flask, Flask-Login
- **Database:** MySQL (via `PyMySQL`)
- **Security:** Werkzeug password hashing
- **Frontend:** Jinja2 templates, HTML/CSS, vanilla JavaScript

## Project Structure

```
finance_app/
├── app.py                 # Flask application: routes, auth, and business logic
├── templates/              # Jinja2 HTML templates
│   ├── Base.html            # Shared layout/navigation
│   ├── login.html / register.html / logout.html
│   ├── dashboard.html       # Landing page after login
│   ├── expenses.html        # Expense CRUD
│   ├── allotment.html       # Budget CRUD
│   ├── advisory.html        # Budget vs. spend report
│   ├── activities.html      # Activity feed
│   ├── chat.html            # Group list / creation
│   ├── group_chat.html      # Individual group chat window
│   └── profile.html         # Account settings
├── static/
│   └── css/style.css        # App styling
└── launch.json              # VS Code debug configuration
```

## Database Schema

The app expects a MySQL database named `finance_app` with the following tables:

```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    note VARCHAR(255),
    date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category VARCHAR(100) NOT NULL,
    monthly_limit DECIMAL(10,2) NOT NULL,
    UNIQUE KEY uniq_user_category (user_id, category),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE `groups` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    owner_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE group_members (
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES `groups`(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE group_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES `groups`(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Getting Started

### Prerequisites
- Python 3.8+
- MySQL Server

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Muaz1307/finance_app.git
   cd finance_app
   ```

2. Install dependencies:
   ```bash
   pip install flask flask-login pymysql werkzeug
   ```

3. Create the MySQL database and tables:
   ```bash
   mysql -u root -p -e "CREATE DATABASE finance_app;"
   mysql -u root -p finance_app < schema.sql
   ```

4. Update the database credentials in `app.py` (`get_db()`) to match your local MySQL setup.

5. Run the app:
   ```bash
   python app.py
   ```

6. Visit `http://127.0.0.1:5000` in your browser.

## Security Notes (for future improvement)

This project was built as a learning/portfolio project. Before any production use, consider:
- Moving the `secret_key` and DB credentials into environment variables rather than hardcoding them in `app.py`.
- Adding CSRF protection (e.g. `Flask-WTF`).
- Parameterizing/validating all user input further and adding rate-limiting on auth routes.
- Replacing the polling-based group chat with WebSockets (e.g. `Flask-SocketIO`) for real-time messaging.

## License

This project is available for personal and educational use.
