# app.py

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
    UserMixin
)
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
from datetime import date

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this!

# Flask-Login setup
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Database helper
def get_db():
    return pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='',
        db='finance_app',
        cursorclass=pymysql.cursors.DictCursor
    )

# User model
class User(UserMixin):
    def __init__(self, data):
        self.id = data['id']
        self.username = data['username']

@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    with db:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            user = cur.fetchone()
    return User(user) if user else None

# Authentication Routes

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        pw_hash = generate_password_hash(password)
        db = get_db()
        with db:
            with db.cursor() as cur:
                try:
                    cur.execute(
                        "INSERT INTO users (username,password_hash) VALUES (%s,%s)",
                        (username, pw_hash)
                    )
                    db.commit()
                    flash('Registered! Please log in.', 'success')
                    return redirect(url_for('login'))
                except pymysql.err.IntegrityError:
                    flash('Username already taken.', 'danger')
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        db = get_db()
        with db:
            with db.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE username=%s", (username,))
                user = cur.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            login_user(User(user))
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Homepage & Financial Routes
@app.route('/')
@login_required
def dashboard():
    db = get_db()
    with db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM expenses WHERE user_id=%s ORDER BY date DESC",
                (current_user.id,)
            )
            recent = cur.fetchall()
    return render_template('dashboard.html', expenses=recent)

# Expence Management
@app.route('/expenses', methods=['GET','POST'])
@login_required
def expenses():
    db = get_db()
    if request.method == 'POST':
        cat = request.form['category']
        amt = request.form['amount']
        note = request.form.get('note','')
        dt = request.form.get('date', date.today())
        with db:
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO expenses (user_id,category,amount,note,date) VALUES (%s,%s,%s,%s,%s)",
                    (current_user.id, cat, amt, note, dt)
                )
                db.commit()
        flash('Expense recorded.', 'success')
    with db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM expenses WHERE user_id=%s ORDER BY date DESC",
                (current_user.id,)
            )
            rows = cur.fetchall()
    return render_template('expenses.html', expenses=rows)

@app.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    db = get_db()
    with db:
        with db.cursor() as cur:
            cur.execute(
                "DELETE FROM expenses WHERE id=%s AND user_id=%s",
                (expense_id, current_user.id)
            )
            db.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('expenses'))

# Budget Management
@app.route('/allotment', methods=['GET','POST'])
@login_required
def allotment():
    db = get_db()
    if request.method == 'POST':
        cat = request.form['category']
        lim = request.form['limit']
        with db:
            with db.cursor() as cur:
                cur.execute("""
                    INSERT INTO budgets (user_id,category,monthly_limit)
                    VALUES (%s,%s,%s)
                    ON DUPLICATE KEY UPDATE monthly_limit=VALUES(monthly_limit)
                """, (current_user.id, cat, lim))
                db.commit()
        flash('Budget updated.', 'success')
    with db:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM budgets WHERE user_id=%s", (current_user.id,))
            rows = cur.fetchall()
    return render_template('allotment.html', budgets=rows)

@app.route('/allotment/delete/<int:budget_id>', methods=['POST'])
@login_required
def delete_budget(budget_id):
    db = get_db()
    with db:
        with db.cursor() as cur:
            cur.execute(
                "DELETE FROM budgets WHERE id=%s AND user_id=%s",
                (budget_id, current_user.id)
            )
            db.commit()
    flash('Budget deleted.', 'success')
    return redirect(url_for('allotment'))

@app.route('/activities', methods=['GET', 'POST'])
@login_required
def activities():
    db = get_db()
    with db:
        with db.cursor() as cur:
            # Insert a new activity if it's a POST request
            if request.method == 'POST':
                content = request.form['content']
                cur.execute(
                    "INSERT INTO activities (user_id,content) VALUES (%s,%s)",
                    (current_user.id, content)
                )
                db.commit()
                flash('Posted.', 'success')

            # Fetch all activities
            cur.execute("""
                SELECT a.*, u.username
                FROM activities a
                JOIN users u ON a.user_id=u.id
                ORDER BY a.timestamp DESC
                LIMIT 50
            """)
            posts = cur.fetchall()

    return render_template('activities.html', posts=posts)

# Group Hub: list & create groups

@app.route('/chat', methods=['GET','POST'])
@login_required
def chat():
    db = get_db()
    # Create new group
    if request.method == 'POST' and 'create_group' in request.form:
        name = request.form['group_name'].strip()
        members = [u.strip() for u in request.form.get('members','').split(',') if u.strip()]
        with db:
            with db.cursor() as cur:
                # insert group
                cur.execute(
                    "INSERT INTO groups (name, owner_id) VALUES (%s,%s)",
                    (name, current_user.id)
                )
                gid = cur.lastrowid
                # add owner
                cur.execute(
                    "INSERT INTO group_members (group_id,user_id) VALUES (%s,%s)",
                    (gid, current_user.id)
                )
                # add others
                for uname in members:
                    cur.execute("SELECT id FROM users WHERE username=%s", (uname,))
                    row = cur.fetchone()
                    if row:
                        cur.execute(
                            "INSERT IGNORE INTO group_members (group_id,user_id) VALUES (%s,%s)",
                            (gid, row['id'])
                        )
                db.commit()
        flash(f'Group "{name}" created.', 'success')
        return redirect(url_for('chat'))

    # Fetch ALL groups the user belongs to
    with db:
        with db.cursor() as cur:
            cur.execute("""
                SELECT
                g.id,
                g.name,
                COUNT(m2.user_id) AS member_count
                FROM group_members AS m
                JOIN groups AS g
                ON m.group_id = g.id
                LEFT JOIN group_members AS m2
                ON g.id = m2.group_id
                WHERE m.user_id = %s
                GROUP BY g.id, g.name
                ORDER BY g.created_at DESC
            """, (current_user.id,))
            groups = cur.fetchall()
    return render_template('chat.html', groups=groups)

# Group-specific chat

@app.route('/groups/<int:group_id>')
@login_required
def group_chat(group_id):
    db = get_db()
    with db:
        with db.cursor() as cur:
            cur.execute("SELECT * FROM groups WHERE id=%s", (group_id,))
            group = cur.fetchone()
    return render_template('group_chat.html', group=group)

@app.route('/groups/<int:group_id>/messages', methods=['GET','POST'])
@login_required
def group_messages(group_id):
    db = get_db()
    if request.method == 'POST':
        msg = request.json.get('message')
        with db:
            with db.cursor() as cur:
                cur.execute(
                    "INSERT INTO group_messages (group_id,user_id,content) VALUES (%s,%s,%s)",
                    (group_id, current_user.id, msg)
                )
                db.commit()
        return jsonify(status='ok')
    else:
        with db:
            with db.cursor() as cur:
                cur.execute("""
                    SELECT gm.content, gm.timestamp, u.username
                    FROM group_messages gm
                    JOIN users u ON gm.user_id=u.id
                    WHERE gm.group_id=%s
                    ORDER BY gm.timestamp DESC
                    LIMIT 50
                """, (group_id,))
                msgs = cur.fetchall()
        return jsonify(msgs[::-1])

# Financial Advisory

@app.route('/advisory')
@login_required
def advisory():
    db = get_db()
    first = date.today().replace(day=1)
    advice = []
    with db:
        with db.cursor() as cur:
            cur.execute(
                "SELECT category, monthly_limit FROM budgets WHERE user_id=%s",
                (current_user.id,)
            )
            for b in cur.fetchall():
                cur.execute("""
                    SELECT SUM(amount) AS spent
                    FROM expenses
                    WHERE user_id=%s AND category=%s AND date>=%s
                """, (current_user.id, b['category'], first))
                spent = cur.fetchone()['spent'] or 0
                if spent > b['monthly_limit']:
                    diff = spent - b['monthly_limit']
                    advice.append(f"Exceeded {b['category']} by {diff:.2f}.")
                else:
                    rem = b['monthly_limit'] - spent
                    advice.append(f"{b['category']}: {rem:.2f} remaining.")
    return render_template('advisory.html', advice=advice)

# Profile (update username/password)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST' and request.form.get('update_profile'):
        print("DEBUG: Received POST request.")

        # Gather & sanitize inputs
        new_username = request.form['new_username'].strip()
        current_password = request.form['current_password'].strip()
        new_password = request.form['new_password'].strip()
        print("DEBUG: Current username:", current_user.username)
        print("DEBUG: New username:", new_username)

        # Open a single connection & cursor
        conn = get_db()
        cur = conn.cursor()

        # Verify the user’s current password
        cur.execute(
            "SELECT password_hash FROM users WHERE id=%s",
            (current_user.id,)
        )
        record = cur.fetchone()
        if not record or not check_password_hash(record['password_hash'], current_password):
            flash('Current password is incorrect.', 'danger')
            cur.close()
            conn.close()
            return redirect(url_for('profile'))

        updated = False

        # Update username if it’s actually changed
        if new_username and new_username != current_user.username:
            try:
                cur.execute(
                    "UPDATE users SET username=%s WHERE id=%s",
                    (new_username, current_user.id)
                )
                print("DEBUG: Username updated in the database.")
                updated = True
            except pymysql.err.IntegrityError:
                flash('That username is already taken.', 'danger')
                cur.close()
                conn.close()
                return redirect(url_for('profile'))

        # Update password if a new one was provided
        if new_password:
            new_hash = generate_password_hash(new_password)
            cur.execute(
                "UPDATE users SET password_hash=%s WHERE id=%s",
                (new_hash, current_user.id)
            )
            updated = True

        # Commit if anything changed
        if updated:
            conn.commit()
            # Refresh the current_user object
            cur.execute("SELECT * FROM users WHERE id=%s", (current_user.id,))
            updated_user = cur.fetchone()
            print("DEBUG: Updated user fetched from the database:", updated_user)
            login_user(User(updated_user))  # Refresh the session
            print("DEBUG: Current user after refresh:", current_user.username)
            flash('Profile updated successfully.', 'success')
        else:
            flash('No changes detected.', 'info')

        # Clean up and redirect
        cur.close()
        conn.close()
        return redirect(url_for('profile'))

    # GET requests just render the form
    return render_template('profile.html')


if __name__ == '__main__':
    app.run(debug=True)
