# ERPX — ERP Management Platform

ERPX is a modular, enterprise-grade ERP platform built with Django. Designed for flexibility, scalability, and ease of use, ERPX helps organizations streamline operations across Finance, Leasing, Human Resources, CRM, and more.

---

![Screenshot 2025-04-10 113720](https://github.com/user-attachments/assets/6bf4e283-e875-4656-84b3-2881f210afb8)
![Screenshot 2025-04-10 153015](https://github.com/user-attachments/assets/326b495f-02d2-446c-a87c-daca425efe70)
![image](https://github.com/user-attachments/assets/38c32c1b-20dc-4e5a-9bfd-7e0dea0d4c25)
![image](https://github.com/user-attachments/assets/a3826a8d-4362-45de-b179-c346c704b338)
![finx](https://github.com/user-attachments/assets/5c1779ba-a16a-4378-9ee8-7bc82fed8129)

---

## 🧹 What is ERPX?

ERPX (Enterprise Resource Planning eXtended) is a full-featured, modular ERP system tailored for startups, SMEs, and growing businesses. It covers critical business needs such as financial accounting, leasing/contract management, HR automation, and customer relationship handling. Built on Django and Python, it supports modern UX, PDF automation, and multilingual (Arabic included) capabilities.

---

## 🧹 Core Modules

### 🔹 FINX - Financial Management
- Invoice & expense tracking
- Chart of accounts, journal entries
- Multi-currency, VAT handling
- Automated recurring invoices

### 🔹 LAMX - Lease & Asset Management
- Contract creation & termination
- Automated PDF generation (agreements, evacuations)
- Business incubator slot assignment
- API integration with external contract data

### 🔹 HRMX - Human Resource Management
- Employee profiles
- Attendance, leaves, offboarding, onboarding
- Payroll integration

### 🔹 CRMX - Customer Relationship Management
- Lead/customer capture
- Company details, contact person roles
- Assign leads to employees

---

## 💡 Features

- Modular structure (plug & play)
- Dynamic forms and filters
- PDF generation (ReportLab, PyPDF2)
- Multilingual support with Arabic reshaping
- Full admin backend + custom dashboards
- Notification center
- API integration (for contracts)
- Docker-ready
- SQLite by default, supports PostgreSQL, MySQL

---

## 🛠 Technologies Used

- Django 4.2
- Python 3.12
- HTML5 / CSS3 / Bootstrap 5
- JavaScript / Chart.js
- PostgreSQL / SQLite
- ReportLab / PyPDF2
- Docker & Docker Compose

---

## 🚀 Installation & Setup

### 1. Clone the Repo
```bash
git clone https://github.com/ahmadrzaa/ERPX.git
cd ERPX
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Linux/macOS
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Database Setup
```bash
python manage.py migrate
```

### 5. Load Demo/Test Database (Optional)
- Use `TestDB_erpx.sqlite3` or data from `load_data/`

### 6. Run the Project
```bash
python manage.py runserver
```

Access the project: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔐 Admin Demo Credentials

If you're using the preloaded database:
```
Username: ERPXadmin
Password: Admin@123
```

---

## 📂 Folder Structure (Highlights)
```
ERPX/
├── finx/            # Financial module
├── lamx/            # Lease & contracts
├── hrmx/            # HR module
├── crmx/            # CRM module
├── templates/       # HTML templates
├── static/          # Static files (CSS/JS/images)
├── media/           # Uploaded media
├── load_data/       # Demo/test data
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🔹 Author

Created and maintained by **Ahmad Raza**  
GitHub: [@ahmadrzaa](https://github.com/ahmadrzaa)

---

## 📜 License

Licensed under the **LGPL-2.1 License**. See [LICENSE](./LICENSE) file.

---

> ERPX is under active development — your contributions, stars, and feedback are welcome!

