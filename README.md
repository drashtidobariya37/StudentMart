# Student Mart 🎓
> **Gujarat-Focused, India-Wide Student Campus Marketplace**  
> *A Third-Year B.Tech Computer Engineering Capstone Project*

Student Mart is a full-stack peer-to-peer campus marketplace designed specifically for verified university students. The platform prioritizes students in **Gujarat, especially Ahmedabad and Gandhinagar**, while connecting campuses seamlessly across all Indian states.

Students can **buy, sell, give away for free, or lend and borrow** second-hand engineering textbooks, GTU notes, Casio scientific calculators, lab coats, mini drafters, electronics, hostel essentials, and campus project components within their university grounds.

---

## 🌟 Key Highlights & Academic Objectives

### 1. Gujarat Focus & India-Wide Scalability
- **Primary Regional Focus:** Prioritizes campuses across **Ahmedabad & Gandhinagar** (Nirma University, DA-IICT, IIT Gandhinagar, PDEU, LD College of Engineering (LDCE), VGEC Chandkheda, Ahmedabad University).
- **Other Gujarat Hubs:** Surat (SVNIT), Vadodara (MSU Baroda), Rajkot, Anand (BVM Vidyanagar), Mehsana, Bhavnagar.
- **India-Wide Coverage:** Supports all Indian states (Maharashtra, Karnataka, Delhi, Tamil Nadu, etc.) with real database-driven counts and no artificially invented inventory.
- **Default Browsing Experience:** Sets Gujarat as the default state for new users, with an instant interactive location switcher in the navigation bar and an optional privacy-safe browser geolocation detector.

### 2. Functional "Urgent Need" Emergency Requests
- **Exam & Practical Lifesaver:** Post requests in 30 seconds for items needed immediately before exams or lab sessions (e.g., *"Need Casio fx-991EX before 10:30 AM GTU exam"*, *"Need XL lab coat for 2 PM practical"*).
- **Urgency Tiers with Automated Expiry:**
  - `Within 1 hour`: 60-minute countdown with pulse indicator
  - `Today`: 6-hour countdown
  - `Tomorrow`: 24-hour deadline
  - `Flexible`: 7-day duration
- **Student Help Offers:** Peers submit private help offers specifying availability, meetup spot, and fee (or free campus help).
- **In-App Alerts:** Requester is alerted in real-time, can review student offers, and accept an offer with one click (marking the request Fulfilled).
- **Trust & Anti-Cheating Moderation:** Dedicated admin moderation queue to flag or reject inappropriate or cheating-related requests.

### 3. Three Flexible Student Exchange Models
- **Buy & Sell:** Hand off semester gear at 40–70% below MRP via safe campus daylight meetup.
- **Free Giveaways:** Seniors pass down handwritten notes, solved question banks, and lab coats to juniors at ₹0.
- **Peer Lending & Borrowing:** Borrow calculators, drafters, or multimeters for exam/practical week with transparent return dates, condition expectations, and refundable security deposits.

### 4. Transparent Verification & Privacy First
- **No Fake Google Logins:** Genuine Google OAuth 2.0 / OpenID Connect integration when credentials are configured in `.env`, with a clear Setup Guide modal when unconfigured.
- **Distinct Trust Badges:** Explicitly distinguishes `Verified Student` (admin approved), `College Email Confirmed` (official campus domain), and `Google Auth`.
- **Privacy by Default:** Student phone numbers and emails are never exposed on public listing cards. Inquiries occur via private in-app buyer-seller chat threads.

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
|---|---|---|
| **Backend** | Python 3.11 + Flask | Modular Application Factory with Blueprints (`main`, `auth`, `listings`, `urgent`, `messages`, `orders`, `admin`) |
| **Database** | SQLite + Flask-SQLAlchemy | Relational models with foreign keys, indexes, and safe auto-migrations (`ensure_schema_upgrades`) |
| **Frontend** | HTML5, Modern CSS3, Vanilla JS | Navy (`#0f172a`), deep indigo, and teal (`#0d9488`) design system with mobile drawer |
| **Authentication** | Server-side secure sessions | Werkzeug password hashing (scrypt/PBKDF2), session cookies (`HttpOnly`, `SameSite=Lax`) |
| **Security** | CSRF & Rate Limiting | Custom token validation on all mutating methods + in-memory IP rate limiter |
| **Payments** | Campus Escrow & Razorpay Sandbox | Simulated student escrow lifecycle + official Razorpay HMAC-SHA256 signature verification |
| **Testing** | Pytest | 28 automated tests covering auth, urgent feed, offers, location switching, orders & payments |

---

## 📂 Project Directory Structure

```text
student_mart/
├── app/
│   ├── __init__.py             # Flask app factory, safe DB schema upgrades, template context processor
│   ├── config.py               # Environment configuration (Dev, Test, Prod)
│   ├── models.py               # SQLAlchemy ORM models (UrgentRequest, UrgentOffer, Notification, Listing, User, etc.)
│   ├── routes/
│   │   ├── main.py             # Home (Gujarat priority), location switcher, notifications, About, Safety
│   │   ├── urgent.py           # Urgent need feed, create, detail, student offers, accept, status toggles
│   │   ├── listings.py         # Catalog browse, search, filters (Gujarat hubs, modes), CRUD
│   │   ├── auth.py             # Login, register, profile with location preference, Google OAuth
│   │   ├── messages.py         # Private buyer-seller conversations, real-time polling
│   │   ├── orders.py           # Order lifecycle (PENDING -> ACCEPTED -> COMPLETED), escrow
│   │   └── admin.py            # Moderation dashboard, urgent queue, listings review, disputes
│   ├── utils/
│   │   ├── auth.py             # Login & admin decorators, session management
│   │   ├── csrf.py             # Cryptographic CSRF token generator & validator
│   │   ├── security.py         # Safe file uploads (UUID filenames), rate limiting
│   │   └── payment.py          # Razorpay signature verification & demo escrow processor
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css        # Typography, CSS variables, navbar, footer, buttons
│   │   │   ├── components.css  # Urgent cards, location dropdown, product cards, chat bubbles
│   │   │   └── pages.css       # Hero section, urgent grid, city hubs layout
│   │   ├── js/
│   │   │   ├── main.js         # Location switcher dropdown, browser geolocation detector, modals
│   │   │   └── chat.js         # Buyer-seller messaging auto-refresh
│   │   ├── img/placeholders/   # Custom category SVG icons (calculator, book, lab, laptop, etc.)
│   │   └── uploads/            # Secure student uploads storage (urgent photos, listings, avatars)
│   └── templates/
│       ├── base.html           # Master layout with location switcher pill, urgent link, notification bell
│       ├── index.html          # Homepage with Gujarat spotlight, urgent feed, city cards
│       ├── notifications.html  # Student alerts dashboard
│       ├── urgent/             # Urgent need feed, post form, detail & offers, my requests
│       ├── listings/           # Catalog browse, detail, sell/lend item, edit, my listings
│       ├── auth/               # Login (1-click evaluation profiles), register, profile
│       ├── messages/           # Inbox and conversation chat
│       ├── orders/             # Order timeline, escrow checkout, dispute management
│       └── admin/              # Dashboard, urgent moderation queue, listings, reports
├── tests/
│   ├── conftest.py             # Pytest fixtures (in-memory SQLite DB, client)
│   ├── test_urgent.py          # Urgent request lifecycle, expiry math, offers, location switcher
│   ├── test_auth.py            # Password hashing, registration, login/logout
│   ├── test_listings.py        # Listing creation, validation, ownership checks
│   ├── test_messaging.py       # Message exchange and third-party privacy isolation
│   ├── test_orders.py          # State transitions (PENDING -> ACCEPTED -> COMPLETED)
│   └── test_payments.py        # HMAC-SHA256 signature verification & dispute resolution
├── instance/                   # Local SQLite database
├── seed_data.py                # Seeds Gujarat colleges, demo listings, urgent needs, offers
├── create_admin.py             # CLI utility to safely provision administrator accounts
├── run.py                      # Local server entrypoint (Port 8000)
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
└── README.md                   # Full documentation
```

---

---

## 🌐 Public Internet Deployment & Sharing

You can make Student Mart accessible to anyone online on their laptop or mobile phone using any of the following verified options:

### Option A: Free 24/7 Cloud Hosting on Render (Recommended)
1. Push your project to a GitHub repository:
   ```powershell
   git init
   git add .
   git commit -m "Initial commit for Student Mart"
   git branch -M main
   git remote add origin https://github.com/<your-username>/student-mart.git
   git push -u origin main
   ```
2. Go to [render.com](https://render.com) and log in with your GitHub account.
3. Click **New +** $\rightarrow$ **Web Service**.
4. Select your `student-mart` repository.
5. Configure the deployment settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn wsgi:app`
6. Under **Environment Variables**, add:
   - `FLASK_ENV`: `production`
   - `SECRET_KEY`: *(Click Generate or enter a secure random string)*
   - `SESSION_COOKIE_SECURE`: `true`
   *(Database and colleges auto-seed automatically on initial launch).*
7. Click **Deploy Web Service**. Within 2 minutes, Render will assign you a live HTTPS link (e.g., `https://student-mart.onrender.com`) that anyone can open from any mobile or laptop.

---

### Option B: Instant Public Sharing from Your Laptop (Zero Deployment Needed)
If you want to share a public link right now while running the project on your laptop:

#### Method 1: Using Cloudflare Tunnel (Free, No Signup, Fast HTTPS)
1. Download `cloudflared` from [developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) or run:
   ```powershell
   winget install --id Cloudflare.cloudflared
   ```
2. Start Student Mart in one terminal:
   ```powershell
   python run.py
   ```
3. In a second terminal, run:
   ```powershell
   cloudflared tunnel --url http://127.0.0.1:8000
   ```
4. Cloudflare will output a public HTTPS link (e.g. `https://random-words.trycloudflare.com`). Send this link to anyone to browse, register, and test the website live from their phone or computer!

#### Method 2: Using ngrok
1. Run:
   ```powershell
   ngrok http 8000
   ```
2. Copy the generated `https://xxxx.ngrok-free.app` URL and share it.

---

### Option C: Mobile Access over Same Wi-Fi / Hotspot
To view and test the website on your smartphone without uploading to the internet:
1. Connect your laptop and phone to the same Wi-Fi (or turn on your phone's Wi-Fi hotspot and connect your laptop).
2. Start the server with the `--public` flag:
   ```powershell
   python run.py --public
   ```
3. The console will display your local network IP (e.g., `http://192.168.1.15:8000`).
4. Type that address into your phone's mobile browser (Chrome/Safari) to access Student Mart directly!

---

### Option D: Local Production Serving with Waitress (Windows)
To run with a multithreaded production WSGI server on Windows without the Flask development server:
```powershell
waitress-serve --port=8000 wsgi:app
```

---

## ⚡ Exact Windows Commands to Run Locally

Follow these exact commands in **Windows PowerShell** or **Command Prompt** to run Student Mart:

### Step 1: Open PowerShell and Navigate to the Project
```powershell
cd "C:\Users\DELL\.gemini\antigravity\scratch\student_mart"
```

### Step 2: Ensure Dependencies Are Installed
```powershell
pip install -r requirements.txt
```

### Step 3: Seed the Gujarat-Focused Database
```powershell
python seed_data.py
```
*(This sets up Gujarat universities including Nirma, DA-IICT, IIT Gandhinagar, LDCE, PDEU, realistic demo items, active urgent requests, and evaluation accounts).*

### Step 4: Run the Flask Web Application
```powershell
python run.py
```

### Step 5: Open in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 🔑 1-Click Evaluation Accounts

On the `/login` page, you can click any of the **1-Click Evaluation Profiles** to test permissions instantly:

| Role | Campus / Location | Email | Password |
|---|---|---|---|
| **Platform Admin** | Nirma University, Ahmedabad | `admin@studentmart.campus` | `Admin@123` |
| **Gujarat Seller** | Nirma University, Ahmedabad | `aarav.sharma@nirmauni.ac.in` | `Student@123` |
| **Gujarat Buyer** | DA-IICT, Gandhinagar | `sneha.patel@daiict.ac.in` | `Student@123` |
| **National Student** | IIT Bombay, Mumbai | `rohan.verma@iitb.ac.in` | `Student@123` |

---

## 🧪 Running Automated Tests

Run the full automated test suite (28 tests) with:
```powershell
pytest -v
```

All 28 tests cover:
- Authentication & password hashing
- Urgent request posting & mathematical expiry calculations
- Student help offer submission & acceptance notifications
- Location switching (Ahmedabad, Gandhinagar, Gujarat, India-wide)
- Peer lending & security deposit management
- Escrow order lifecycle and Razorpay HMAC signature validation

---

## 🛡️ Campus Trust & Safety Protocols
- **Daylight Public Meeting Spots:** Central Library porch, student canteen, or department quadrangle.
- **Prohibited Items Policy:** Strict ban on test cheat materials, institutional property, and hazardous goods.
- **Peer Lending Transparency:** Transparent security deposits, clear duration expectations, and peer-to-peer verification.
- **Dispute Resolution:** In-app dispute filing with administrative escrow arbitration.

---
*Developed with Python Flask, SQLite, and Vanilla Web Technologies for academic evaluation.*
