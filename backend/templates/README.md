# 💧 Smart Water Guardian

A Flask-based web application that allows citizens to report water leakage complaints online. The system provides separate dashboards for users and administrators to manage reports efficiently.

---

## 📌 Features

### 👤 User

- User Registration
- Secure Login & Logout
- Forgot Password
- Submit Water Leakage Report
- Upload Leakage Images
- View Personal Reports
- Search Reports
- Filter Reports
- Dashboard Statistics

### 👑 Admin

- Admin Login
- Admin Dashboard
- View All Reports
- Search Reports
- Update Report Status
- Delete Reports
- User Management
- Delete Users
- Export Reports as CSV
- Charts & Analytics

---

## 🛠 Tech Stack

### Frontend

- HTML5
- CSS3
- Bootstrap 5
- JavaScript
- Chart.js

### Backend

- Python
- Flask

### Database

- MySQL

### Deployment

- Render
- Aiven MySQL

---

## 📂 Project Structure

```
SmartWaterGuardian/
│
├── backend/
│   ├── app.py
│   ├── templates/
│   ├── static/
│   │   ├── css/
│   │   ├── uploads/
│   │   └── images/
│
├── requirements.txt
├── README.md
└── database.sql
```

---

## ⚙ Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/SmartWaterGuardian.git
```

### Open Project

```bash
cd SmartWaterGuardian/backend
```

### Create Virtual Environment

```bash
python -m venv .venv
```

### Activate

Windows

```bash
.venv\Scripts\activate
```

Linux/Mac

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Application

```bash
python app.py
```

---

## 🗄 Database

Create a MySQL database and import:

```
database.sql
```

Update your database credentials inside:

```
backend/app.py
```

or your `.env` file if used.

---

## 📊 Modules

- Home
- Login
- Registration
- Forgot Password
- User Dashboard
- Report Management
- Admin Dashboard
- User Management
- CSV Export
- Analytics Dashboard

---

## 🔐 Security Features

- Password Hashing
- Session Management
- Admin Role Authentication
- User Authorization
- Secure File Upload

---

## 📸 Screenshots

Add screenshots here.

Example:

- Home Page
- Login Page
- User Dashboard
- Report Form
- Admin Dashboard
- User Management
- Analytics Dashboard

---

## 🚀 Future Enhancements

- Email Notifications
- SMS Alerts
- Google Maps Integration
- Live Complaint Tracking
- Mobile Application
- AI-Based Leakage Detection

---

## 👨‍💻 Developer

**Shubham Maurya**

B.Tech Computer Science Engineering

---

## 📄 License

This project is developed for educational and learning purposes.