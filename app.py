# app.py -- SQLite-converted version (full, DB-workable)
import os
import random
import ssl
import smtplib
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import tensorflow as tf
from flask import Flask, g, redirect, render_template, request, session, url_for, flash
from sklearn.preprocessing import StandardScaler
import sqlite3

# ------------------ CONFIG ------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "upi_fraud.sqlite")




# SMTP config (use env in production)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "way2track01@gmail.com")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD", "masvczanrdbufpuq")

# ML files (must exist in repo)
DATASET_CSV = os.path.join(BASE_DIR, "upi_fraud_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model", "project_model2.h5")

# Flask
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "your_super_secret_key_change_this_in_production")

# Globals for ML
model = None
scaler = None

# ------------------ SQLite helpers ------------------
def get_db():
    """Return a connection to the SQLite DB (cached on flask.g)."""
    db = g.get("_sqlite_db", None)
    if db is None:
        conn = sqlite3.connect(SQLITE_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        g._sqlite_db = conn
        db = conn
    return db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop("_sqlite_db", None)
    if db is not None:
        db.close()

def init_db():
    """Create required tables if they don't exist."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()

    # bank_accounts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bank_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        dob TEXT,                 -- stored as 'YYYY-MM-DD'
        mobile_number TEXT UNIQUE,
        email TEXT UNIQUE,
        location TEXT,
        state INTEGER,
        zip INTEGER,
        otp TEXT,
        otp_expiry TEXT,
        creation_date TEXT DEFAULT (datetime('now'))
    );
    """)

    # merchants
    cur.execute("""
    CREATE TABLE IF NOT EXISTS merchants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mobile_number TEXT,
        upi_number TEXT UNIQUE,
        category INTEGER,
        setup_date TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (mobile_number) REFERENCES bank_accounts(mobile_number)
    );
    """)

    # transactions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_mobile TEXT,
        merchant_upi TEXT,
        trans_amount REAL,
        status TEXT,
        trans_hour INTEGER,
        trans_day INTEGER,
        trans_month INTEGER,
        trans_year INTEGER,
        category INTEGER,
        age INTEGER,
        state INTEGER,
        zip INTEGER,
        trans_date TEXT,  -- store date as ISO (YYYY-MM-DD)
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("SQLite DB initialized:", SQLITE_DB)

# ---------------- ML loading ----------------
def load_ml_assets():
    """Load scaler (fit from CSV) and Keras model if available."""
    global model, scaler
    # Load scaler
    try:
        dataset = pd.read_csv(DATASET_CSV)
        x_for_scaling = dataset.iloc[:, :10].values  # match your training order
        scaler = StandardScaler()
        scaler.fit(x_for_scaling)
        print("Scaler fitted successfully.")
    except FileNotFoundError:
        scaler = None
        print(f"Warning: '{DATASET_CSV}' not found. Scaler not loaded.")
    except Exception as e:
        scaler = None
        print(f"Error loading or fitting scaler: {e}")

    # Load model
    try:
        if os.path.exists(MODEL_PATH):
            model = tf.keras.models.load_model(MODEL_PATH)
            print("Model loaded successfully.")
        else:
            model = None
            print(f"Model not found at {MODEL_PATH}")
    except Exception as e:
        model = None
        print(f"Error loading model: {e}")

# ---------------- Helper functions ----------------
def send_otp_email(receiver_email, otp):
    subject = "Your SecurePay OTP Verification"
    body = f"Your One-Time Password (OTP) for SecurePay is: {otp}. It is valid for 5 minutes."
    message = f"Subject: {subject}\n\n{body}"
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, receiver_email, message)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def generate_otp():
    return str(random.randint(100000, 999999))

def parse_iso_datetime(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except Exception:
            try:
                return datetime.strptime(s, "%Y-%m-%d")
            except Exception:
                return None

def predict_fraud(transaction_features):
    """Return 1 for fraud, 0 for valid, -1 on error/missing model."""
    global model, scaler
    if model is None or scaler is None:
        print("ML model or scaler not loaded. Cannot predict fraud.")
        return -1
    try:
        input_array = np.array(transaction_features).reshape(1, -1)
        scaled = scaler.transform(input_array)
        pred = model.predict(scaled)
        # flatten
        if isinstance(pred, np.ndarray):
            p = pred.flatten()[0]
        else:
            p = float(pred)
        fraud_risk = 1 if p > 0.5 else 0
        return fraud_risk
    except Exception as e:
        print(f"Error during fraud prediction: {e}")
        return -1

# ---------------- Routes ----------------
@app.route('/')
def index():
    return render_template('index.html')

# ---------- Login (user via mobile+OTP; admin via username/password) ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'mobile' in session:
        t = session.get('user_type')
        if t == 'user':
            return redirect(url_for('user_dashboard'))
        if t == 'merchant':
            return redirect(url_for('merchant_dashboard'))
        if t == 'admin':
            return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        form_type = request.form.get('form_type')
        conn = get_db()
        cur = conn.cursor()
        if form_type == 'user':
            mobile_number = request.form.get('mobile_number')
            if not mobile_number:
                flash('Mobile number is required for user login.', 'danger')
                cur.close()
                return render_template('login.html')
            try:
                cur.execute("SELECT * FROM bank_accounts WHERE mobile_number = ?", (mobile_number,))
                user = cur.fetchone()
                if user:
                    otp = generate_otp()
                    otp_expiry = (datetime.now() + timedelta(minutes=5)).isoformat()
                    cur.execute("UPDATE bank_accounts SET otp = ?, otp_expiry = ? WHERE mobile_number = ?",
                                (otp, otp_expiry, mobile_number))
                    conn.commit()
                    if send_otp_email(user["email"], otp):
                        session['mobile'] = mobile_number
                        session['user_type'] = 'user'
                        flash('OTP sent to your registered email. Please verify to log in.', 'info')
                        cur.close()
                        return redirect(url_for('verify_otp', mobile=mobile_number))
                    else:
                        flash('Failed to send OTP. Please try again.', 'danger')
                else:
                    flash('User account not found. Please register.', 'danger')
            except Exception as e:
                flash(f'Database error: {e}', 'danger')
            finally:
                cur.close()

        elif form_type == 'admin':
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                flash('Username and password are required for admin login.', 'danger')
                return render_template('login.html')
            if username == 'admin' and password == 'admin':
                session['mobile'] = '0000000000'
                session['user_type'] = 'admin'
                flash('Admin login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Invalid admin credentials.', 'danger')
        else:
            flash('Invalid form submission.', 'danger')

    return render_template('login.html')

@app.route('/verify_otp/<mobile>', methods=['GET', 'POST'])
def verify_otp(mobile):
    if 'mobile' not in session or session['mobile'] != mobile:
        flash('Invalid request. Please log in again.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_otp = request.form.get('otp')
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("SELECT otp, otp_expiry FROM bank_accounts WHERE mobile_number = ?", (mobile,))
            row = cur.fetchone()
            if row:
                stored_otp = row["otp"]
                expiry_raw = row["otp_expiry"]
                expiry_dt = parse_iso_datetime(expiry_raw)
                if stored_otp == user_otp and expiry_dt and expiry_dt > datetime.now():
                    cur.execute("UPDATE bank_accounts SET otp = NULL, otp_expiry = NULL WHERE mobile_number = ?", (mobile,))
                    conn.commit()
                    cur.execute("SELECT * FROM merchants WHERE mobile_number = ?", (mobile,))
                    merchant_info = cur.fetchone()
                    if merchant_info:
                        session['user_type'] = 'merchant'
                        flash('Login successful as Merchant!', 'success')
                        cur.close()
                        return redirect(url_for('merchant_dashboard'))
                    else:
                        session['user_type'] = 'user'
                        flash('Login successful as User!', 'success')
                        cur.close()
                        return redirect(url_for('user_dashboard'))
                elif expiry_dt and expiry_dt <= datetime.now():
                    flash('OTP has expired. Please log in again to get a new OTP.', 'danger')
                    cur.close()
                    return redirect(url_for('login'))
                else:
                    flash('Invalid OTP. Please try again.', 'danger')
            else:
                flash('User not found. Please register.', 'danger')
        except Exception as e:
            flash(f'Database error: {e}', 'danger')
        finally:
            cur.close()

    return render_template('verify_otp.html', mobile=mobile)

# ---------- Registration ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        dob_str = request.form.get('dob')
        mobile_number = request.form.get('mobile_number')
        email = request.form.get('email')
        location = request.form.get('location')
        state = request.form.get('state')
        zip_code = request.form.get('zip')

        if not all([full_name, dob_str, mobile_number, email, location, state, zip_code]):
            flash('All fields are required!', 'danger')
            return render_template('register.html')

        try:
            datetime.strptime(dob_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format for Date of Birth. Please use YYYY-MM-DD.', 'danger')
            return render_template('register.html')

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM bank_accounts WHERE mobile_number = ? OR email = ?", (mobile_number, email))
            if cur.fetchone():
                flash('Mobile number or email already registered.', 'danger')
                return render_template('register.html')
            cur.execute("""
                INSERT INTO bank_accounts (full_name, dob, mobile_number, email, location, state, zip)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (full_name, dob_str, mobile_number, email, location, int(state), int(zip_code)))
            conn.commit()
            flash('Registration successful! You can now log in.', 'success')
            cur.close()
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'An unexpected error occurred: {e}', 'danger')
        finally:
            cur.close()

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# ---------- User pages ----------
@app.route('/user_dashboard')
def user_dashboard():
    if session.get('user_type') not in ['user', 'merchant']:
        flash('Please log in to access your dashboard.', 'warning')
        return redirect(url_for('login'))

    user_mobile = session['mobile']
    conn = get_db()
    cur = conn.cursor()
    user_info = None
    try:
        cur.execute("SELECT * FROM bank_accounts WHERE mobile_number = ?", (user_mobile,))
        row = cur.fetchone()
        user_info = dict(row) if row else None
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
    finally:
        cur.close()
    return render_template('user.html', user=user_info)

@app.route('/user/profile')
def user_profile_page():
    if session.get('user_type') not in ['user', 'merchant']:
        flash('Please log in to view your profile.', 'warning')
        return redirect(url_for('login'))

    user_mobile = session.get('mobile')
    if not user_mobile:
        flash('Session error: Mobile number missing.', 'danger')
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()
    user_info = None
    try:
        cur.execute("SELECT * FROM bank_accounts WHERE mobile_number = ?", (user_mobile,))
        row = cur.fetchone()
        user_info = dict(row) if row else None
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
    finally:
        cur.close()
    return render_template('user_profile_page.html', user=user_info)

@app.route('/user/make_payment', methods=['GET'])
def user_make_payment_page():
    if session.get('user_type') not in ['user', 'merchant']:
        flash('Please log in to make a payment.', 'warning')
        return redirect(url_for('login'))
    return render_template('user_make_payment_page.html')

@app.route('/user/transactions', methods=['GET'])
def user_transactions_page():
    if session.get('user_type') not in ['user', 'merchant']:
        flash('Please log in to view your transactions.', 'warning')
        return redirect(url_for('login'))
    user_mobile = session['mobile']
    conn = get_db()
    cur = conn.cursor()
    transactions = []
    try:
        cur.execute("SELECT * FROM transactions WHERE user_mobile = ? ORDER BY trans_date DESC", (user_mobile,))
        transactions = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
    finally:
        cur.close()
    return render_template('user_transactions_page.html', transactions=transactions)

@app.route('/user/pay', methods=['POST'])
def user_pay():
    if session.get('user_type') not in ['user', 'merchant']:
        flash('Please log in to make a payment.', 'warning')
        return redirect(url_for('login'))

    if scaler is None or model is None:
        flash('Fraud detection system is not fully loaded. Please contact support.', 'danger')
        return redirect(url_for('user_make_payment_page'))

    merchant_upi = request.form.get('merchant_upi')
    try:
        trans_amount = float(request.form.get('trans_amount'))
    except (TypeError, ValueError):
        flash('Invalid transaction amount.', 'danger')
        return redirect(url_for('user_make_payment_page'))

    user_mobile = session['mobile']
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT dob, state, zip FROM bank_accounts WHERE mobile_number = ?", (user_mobile,))
        user_details = cur.fetchone()
        if not user_details:
            flash('User details not found. Cannot process payment.', 'danger')
            cur.close()
            return redirect(url_for('user_make_payment_page'))

        cur.execute("SELECT category FROM merchants WHERE upi_number = ?", (merchant_upi,))
        merchant_details = cur.fetchone()
        if not merchant_details:
            flash('Merchant not found. Please check UPI number.', 'danger')
            cur.close()
            return redirect(url_for('user_make_payment_page'))

        now = datetime.now()
        trans_hour = now.hour
        trans_day = now.day
        trans_month = now.month
        trans_year = now.year
        category = int(merchant_details["category"])

        dob_str = user_details["dob"]
        try:
            dob_dt = datetime.strptime(dob_str, "%Y-%m-%d")
            age = now.year - dob_dt.year - ((now.month, now.day) < (dob_dt.month, dob_dt.day))
        except Exception:
            age = 0

        state = int(user_details["state"]) if user_details["state"] is not None else 0
        zip_code = int(user_details["zip"]) if user_details["zip"] is not None else 0

        transaction_features = [trans_hour, trans_day, trans_month, trans_year, category, 0, age, trans_amount, state, zip_code]

        print("Transaction features (before scaling):", transaction_features)

        # Use predict_fraud which scales and uses model
        fraud_risk = predict_fraud(transaction_features)
        print("Predicted fraud risk:", fraud_risk)

        status = 'FRAUDULENT' if fraud_risk == 1 else 'VALID'
        output_message = "Transaction is VALID and processed securely." if status == 'VALID' else "FRAUDULENT transaction detected! Payment blocked."

        cur.execute("""
            INSERT INTO transactions
            (user_mobile, merchant_upi, trans_amount, status, trans_hour, trans_day, trans_month, trans_year, category, age, state, zip, trans_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_mobile, merchant_upi, trans_amount, status, trans_hour, trans_day, trans_month, trans_year, category, age, state, zip_code, now.date().isoformat()))
        conn.commit()

        cur.close()
        return render_template('result.html', status=status.lower(), OUTPUT=output_message)

    except Exception as e:
        flash(f'An unexpected error occurred: {e}', 'danger')
        print(f"Error in user_pay: {e}")
        cur.close()
        return redirect(url_for('user_make_payment_page'))

# ---------- Admin routes ----------
@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('user_type') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/admin/users')
def admin_users_page():
    if session.get('user_type') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    users = []
    try:
        cur.execute("SELECT * FROM bank_accounts")
        users = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
    finally:
        cur.close()
    return render_template('admin_users.html', users=users)

@app.route('/admin/merchants')
def admin_merchants_page():
    if session.get('user_type') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    merchants = []
    try:
        cur.execute("SELECT * FROM merchants")
        merchants = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
    finally:
        cur.close()
    return render_template('admin_merchants.html', merchants=merchants)

@app.route('/admin/transactions')
def admin_transactions_page():
    if session.get('user_type') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    transactions = []
    try:
        cur.execute("SELECT * FROM transactions ORDER BY trans_date DESC")
        transactions = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
    finally:
        cur.close()
    return render_template('admin_transactions.html', transactions=transactions)

@app.route('/admin/create_account', methods=['GET', 'POST'])
def admin_create_account():
    if session.get('user_type') != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        dob_str = request.form.get('dob')
        mobile_number = request.form.get('mobile_number')
        email = request.form.get('email')
        location = request.form.get('location')
        state = request.form.get('state')
        zip_code = request.form.get('zip')

        if not all([full_name, dob_str, mobile_number, email, location, state, zip_code]):
            flash('All fields are required!', 'danger')
            return render_template('admin_create_account.html')

        try:
            datetime.strptime(dob_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format for Date of Birth. Please use YYYY-MM-DD.', 'danger')
            return render_template('admin_create_account.html')

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO bank_accounts (full_name, dob, mobile_number, email, location, state, zip)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (full_name, dob_str, mobile_number, email, location, int(state), int(zip_code)))
            conn.commit()
            flash('Account created successfully!', 'success')
            cur.close()
            return redirect(url_for('admin_users_page'))
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                flash('Mobile number or email already registered.', 'danger')
            else:
                flash(f'Database error: {e}', 'danger')
        except Exception as e:
            flash(f'An unexpected error occurred: {e}', 'danger')
        finally:
            cur.close()
    return render_template('admin_create_account.html')

# ---------- Merchant routes ----------
@app.route('/merchant_dashboard')
def merchant_dashboard():
    if session.get('user_type') not in ['user', 'merchant']:
        flash('Please log in to access the merchant panel.', 'warning')
        return redirect(url_for('login'))
    merchant_mobile = session['mobile']
    conn = get_db()
    cur = conn.cursor()
    user_info = None
    merchant_info = None
    transactions = []
    try:
        cur.execute("SELECT * FROM bank_accounts WHERE mobile_number = ?", (merchant_mobile,))
        row = cur.fetchone()
        user_info = dict(row) if row else None

        cur.execute("SELECT * FROM merchants WHERE mobile_number = ?", (merchant_mobile,))
        mrow = cur.fetchone()
        merchant_info = dict(mrow) if mrow else None

        if not merchant_info:
            flash('You need to set up your merchant account first.', 'info')
            cur.close()
            return redirect(url_for('merchant_setup'))

        cur.execute("SELECT * FROM transactions WHERE merchant_upi = ? ORDER BY trans_date DESC", (merchant_info['upi_number'],))
        transactions = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
    finally:
        cur.close()
    return render_template('merchant.html', user=user_info, merchant=merchant_info, transactions=transactions)

@app.route('/merchant_setup', methods=['GET', 'POST'])
def merchant_setup():
    if 'user_type' not in session or session['user_type'] not in ['user', 'merchant']:
        flash('Please log in to set up a merchant account.', 'warning')
        return redirect(url_for('login'))
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM merchants WHERE mobile_number = ?", (session['mobile'],))
        if cur.fetchone():
            flash('You already have a merchant account.', 'info')
            cur.close()
            return redirect(url_for('merchant_dashboard'))
    except Exception as e:
        flash(f'Database error: {e}', 'danger')
        cur.close()
        return render_template('merchant_setup.html')

    if request.method == 'POST':
        upi_number = request.form.get('upi_number')
        category = request.form.get('category')
        if not upi_number or not category:
            flash('UPI Number and Category are required.', 'danger')
            cur.close()
            return render_template('merchant_setup.html')
        try:
            cur.execute("INSERT INTO merchants (mobile_number, upi_number, category) VALUES (?, ?, ?)",
                        (session['mobile'], upi_number, int(category)))
            conn.commit()
            session['user_type'] = 'merchant'
            flash('Merchant account created successfully!', 'success')
            cur.close()
            return redirect(url_for('merchant_dashboard'))
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                flash('This UPI number is already taken.', 'danger')
            else:
                flash(f'Database error: {e}', 'danger')
        except Exception as e:
            flash(f'Unexpected error: {e}', 'danger')
        finally:
            cur.close()
    else:
        cur.close()
    return render_template('merchant_setup.html')
# ----------------- App startup -----------------
if __name__ == '__main__':
    # ensure model dir exists
    if not os.path.exists(os.path.join(BASE_DIR, "model")):
        os.makedirs(os.path.join(BASE_DIR, "model"))

    init_db()       # create sqlite file + tables if missing
    load_ml_assets()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
