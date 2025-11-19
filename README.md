
# markdown
# 🔐 SecurePay – UPI Fraud Detection System  
A complete Flask-based UPI payment platform integrated with **Machine Learning–powered Fraud Detection**.  
The system includes **User**, **Merchant**, and **Admin** dashboards, secure authentication, QR-based payments, and real-time fraud prediction.

---

## 🚀 Features

### 👤 User Features
- Login using mobile number (OTP-based flow)
- Make payments through:
  - Manual UPI number entry
  - QR code scanning (jsQR)
- Real-time fraud detection before confirming payment
- Full transaction history with details
- Option to become a merchant

### 🧾 Merchant Features
- Merchant onboarding with UPI setup
- Auto-generated QR Code for receiving payments
- Merchant dashboard with received transactions
- Fraud/legitimate status indicators
- Profile modal with merchant details

### 🛡️ Admin Features
- Admin login
- Create new user accounts
- View all registered users
- View all merchants
- View all transactions with fraud labels
- Detailed modal view for each transaction

---

## 🧠 Machine Learning Model

A trained model predicts whether a UPI transaction is:

✔ **Legitimate**  
❌ **Fraudulent**

### Model Features Used
- Transaction Amount  
- Hour / Day / Month / Year  
- User Age  
- Merchant Category  
- State  
- ZIP  
- User Demographics  

### Model File
- `build_model.ipynb` (training code)
- `fraud_model.pkl` (loaded in Flask)

---

## 📂 Project Structure

```

SecurePay/
│── app.py
│── build_model.ipynb
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── user.html
│   ├── user_make_payment_page.html
│   ├── user_transactions_page.html
│   ├── merchant.html
│   ├── merchant_setup.html
│   ├── admin.html
│   ├── admin_users.html
│   ├── admin_transactions.html
│   ├── admin_create_account.html
│
├── static/
│   ├── img/
│   ├── css/
│   ├── js/
│
├── model/
│   └── fraud_model.pkl
│
├── requirements.txt
└── README.md

````

---

## ▶️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/SecurePay-UPI-Fraud-Detection.git
cd SecurePay-UPI-Fraud-Detection
````

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Setup MySQL Database

Create a database:

```sql
CREATE DATABASE securepay;
```

Update DB config inside **app.py**:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/securepay'
```

### 4️⃣ Run Flask Server

```bash
python app.py
```

### 5️⃣ Open in Browser

```
http://127.0.0.1:5000/
```

---

## 🔐 Default Login Details

### Admin:

```
username: admin
password: admin
```

### User:

Mobile number → OTP generated internally

---

## 🌐 Application Workflow

### ✔ User Flow

1. Login with mobile
2. Dashboard → Make Payment / Transactions
3. Scan QR or manually enter UPI
4. ML fraud detection
5. Payment processed
6. Transaction saved & visible in history

### ✔ Merchant Flow

1. User becomes merchant
2. Creates UPI + category
3. Dashboard shows:

   * Profile
   * QR Code
   * Received transactions

### ✔ Admin Flow

1. Login
2. Create accounts
3. Monitor users, merchants & transactions
4. Check fraud predictions

---

## 🛠 Technologies Used

### Backend

* Python
* Flask
* SQLAlchemy
* Machine Learning Model (RandomForest / XGBoost)

### Frontend

* HTML5
* Bootstrap 5
* CSS
* JavaScript
* jsQR (QR decoding)
* QRCode.js (QR generation)

---

## 👥 Contributors

* **Shivam Swami** – Developer

---

## 📄 License

This project is for educational and academic use.

---

⭐ *If you like this project, kindly star the repository!*

```
