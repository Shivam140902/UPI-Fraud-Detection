```markdown
# 🔐 SecurePay – UPI Fraud Detection System  
A complete web-based UPI payment platform integrated with **Machine Learning-based Fraud Detection**, built using **Flask**, **Bootstrap**, and **Python**.  
Users can make payments securely, merchants can receive payments via QR codes, and admins can manage all accounts and transactions in one system.

---

# 📌 Features Overview

## 👤 **User Features**
- OTP-based login using mobile number  
- Secure dashboard with profile view  
- Make payments via:
  - Manual UPI entry  
  - QR Code scanning (jsQR)  
- Real-time ML-based fraud detection before completing payment  
- Full transaction history  
- Option to register as a merchant

---

## 🧾 **Merchant Features**
- Merchant onboarding with UPI setup  
- Auto-generated QR Code for receiving payments  
- Merchant dashboard with stats  
- Transaction history with fraud status  
- Beautiful modals with profile information  

---

## 🛡️ **Admin Features**
- Admin login  
- Create new user accounts  
- View all users  
- View all merchants  
- Full transaction monitoring  
- Fraudulent vs Non-Fraudulent indicators  
- Detailed transaction modal for analytics  

---

# 🧠 Machine Learning Model
This project uses an ML model trained to classify whether a UPI transaction is:

✔ **Legitimate**  
❌ **Fraudulent**

### **Key Features Used**
- Transaction amount  
- Date & time (hour, day, month, year)  
- User age  
- Merchant category  
- State  
- ZIP  
- User demographic parameters  

### **Model File Used**
```

build_model.ipynb
fraud_model.pkl (if included)

```

The model is loaded in Flask and predicts fraud during each payment.

---

# 📂 Project Structure

```

SecurePay/
│── app.py                     # Main Flask backend
│── build_model.ipynb          # Jupyter notebook to build ML model
│
├── templates/                 # All frontend HTML templates
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
│   ├── img/                   # Backgrounds, icons, illustrations
│   ├── css/                   # Optional custom CSS
│   ├── js/                    # Optional JavaScript files
│
├── model/
│   └── fraud_model.pkl        # ML model file (if used)
│
├── requirements.txt
└── README.md

````

---

# ▶️ How to Run the Project

## **1️⃣ Clone the Repository**
```bash
git clone https://github.com/your-username/SecurePay-UPI-Fraud-Detection.git
cd SecurePay-UPI-Fraud-Detection
````

## **2️⃣ Install Dependencies**

```bash
pip install -r requirements.txt
```

## **3️⃣ Configure MySQL Database**

Create a database and update this line inside `app.py`:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://username:password@localhost/securepay'
```

Run:

```sql
CREATE DATABASE securepay;
```

## **4️⃣ Run the Flask Server**

```bash
python app.py
```

## **5️⃣ Open in Browser**

```
http://127.0.0.1:5000/
```

---

# 🔐 Default Login Credentials

### **Admin Login**

```
Username: admin
Password: admin
```

(or as configured in your code)

### **User Login**

Mobile-based OTP generated internally by backend logic.

---

# 🌐 Application Flow

## ✔ **User Flow**

1. Login using mobile number
2. View dashboard
3. Make payment:

   * Scan QR code OR
   * Enter merchant UPI
4. ML model predicts fraud
5. Transaction saved
6. User can view complete history

## ✔ **Merchant Flow**

1. User registers as merchant
2. Sets UPI & category
3. Dashboard shows:

   * Profile
   * QR code
   * Received payments

## ✔ **Admin Flow**

1. Login using admin credentials
2. Create users
3. Monitor users, merchants, transactions
4. Fraud marked visually using badges
5. Detailed transaction modal

---

# 👨‍💻 Technologies Used

### **Backend**

* Python
* Flask
* SQLAlchemy
* ML Model (RandomForest / XGBoost etc.)

### **Frontend**

* HTML5
* Bootstrap 5
* CSS
* JS (QRCode.js + jsQR)
* Google Fonts

---

# 📄 License

This project is for educational and academic use only.

---

# 🙌 Contributors

* **Shivam Swami** — Developer & Project Lead

---

## ⭐ If you found this useful, don't forget to star the repository!

