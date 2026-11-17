# KainGo – Customer Promotion & Delivery Tracking System

Final Project – IPT1 / OOP / Web Systems and Technologies (Laguna University, College of Computing Studies).

A restaurant ordering website. Customers order like at a kiosk (tap the food, see "Your Order"), choose **Delivery (COD)** or
**Pickup (Cash)**, and the restaurant **calls them to confirm** the order. Customers then follow their **order status**.
The admin handles the confirmation calls, order status, menu, and promos.

**Technology stack (as required):** Backend: Flask (Python) · Frontend: HTML5, CSS3, Bootstrap 5 · JavaScript · Database: MySQL.

## 1. Requirements
- Python 3.10 or newer
- XAMPP (for the MySQL database and, optionally, Apache)
- Python packages in `requirements.txt` (Flask, Flask-WTF, mysql-connector-python)

## 2. Set up and run locally (XAMPP)
1. Open the **XAMPP Control Panel** and **Start** `MySQL`.
2. Install the dependencies (in a terminal inside this folder):
   ```
   pip install -r requirements.txt
   ```
3. Initialize the database (creates `kaingo_db`, the tables, a sample menu, sample promos, and the admin account). Run once:
   ```
   python init_db.py
   ```
   (If you already created the database with an older version of this project, run `python init_db.py --reset` once. It erases the old
   database and creates a fresh one with the new menu options.)
4. Run the app (or double-click `start_kaingo.bat`):
   ```
   python app.py
   ```
5. Open **http://127.0.0.1:5000**

XAMPP's default MySQL login is already set in `config.py` (host `localhost`, user `root`, no password, database `kaingo_db`).
If you set a MySQL password, put it in `DB_PASSWORD` in `config.py`.

| Role  | Email             | Password  |
|-------|-------------------|-----------|
| Admin | admin@kaingo.org  | Admin@123 |

Customers register on the Register page. Change the admin password on the Profile page after the first login.

### Optional: open it at http://localhost through XAMPP's Apache
Apache cannot run Python by itself, so it forwards the pages to the Flask app. Start **Apache** and **MySQL** in XAMPP,
double-click `xampp_setup.bat` once (then Stop/Start Apache), keep `start_kaingo.bat` running, and open **http://localhost**.
If Apache does not start, another program is using port 80 (for example Skype or IIS).

### Emails (SMTP)
The system sends real emails with Python's `smtplib` (welcome email and order status emails). Set `MAIL_USERNAME` and
`MAIL_PASSWORD` (a Gmail App Password) in `config.py` or as environment variables. If they are empty, the emails are printed in the
terminal instead, so the app still works.

## 3. How ordering works (self-ordering kiosk style)
The order page works like a fast-food self-ordering kiosk, with five screens and a bottom order bar:
1. **Start screen:** "Touch one to start your order": **Delivery** (pay by COD) or **Pickup** (pay Cash). There is no delivery fee.
2. **Menu screen:** categories with photos on the left (Silog Meals, Pares & Laga-laga, Ihaw-Ihaw, Pancit, Sides & Pulutan, Ulam,
   Refreshments) and food tiles with **dish photos** on the right. Tap a food to add it. A number badge shows how many are in the order.
3. **Food screen:** foods with options (the fruit smoothie and shake ask for a **flavor**) open a screen to **choose one option**, set the
   quantity, and press **Add To Order**.
4. **Review screen:** the bottom bar shows **YOUR ORDER** with the item count and total, plus **Cancel Order** and **View Order**.
   The review screen lists every line with + / − buttons, then **Add More Items** or **Checkout**.
5. **Details screen:** contact number, delivery address (for Delivery), optional promo code, and the tick-box agreeing to answer the
   confirmation call. Press **Place Order**. The customer gets a big **order number** on the tracking page.

After that:
- The order is **not confirmed yet**: it is saved as **Pending Call**. The admin opens **Orders**, calls the customer, then presses
  **Confirmed**, **No answer** (cancels after 3 missed calls) or **Declined**.
- After **Confirmed**, the admin moves it: Preparing → Out for Delivery / Ready for Pickup → Delivered / Picked Up.
- The customer's tracking page shows a progress bar, the chosen options, and the status history, and refreshes itself every 15 seconds.
  Each change also sends an email.

### The menu and prices
The menu and prices in `database/kaingo_db.sql` come from Panyero's Place's menu boards (silog meals, pares, laga-laga, ihaw-ihaw, pancit,
ulam, sides, and refreshments). The dish photos in `static/img/menu/` were cropped from photos of those boards. Only the clear photos are included (20 of them);
foods whose crop was blurry or had board text on it show an emoji instead, until you upload a better photo in Admin → Menu.
- The **smoothie and shake prices (₱60 and ₱70) are placeholders**, because no price was on their board. Change them in Admin → Menu.
- **Buko Juice** has no photo, so it shows an emoji until you upload one.
- In **Admin → Menu** you can add or edit a food, set its price, upload a **dish photo**, and add **choices** with the *Choices* box,
  for example `Flavor:Mango|Melon|Banana`.

## 4. The 13 required features
| # | Feature | Where |
|---|---------|-------|
| 1 | Own logo & branding | `static/logo.svg` (navbar, favicon, login/register, home), `static/style.css` |
| 2 | Index / home page | `templates/index.html` |
| 3 | Registration | `/register` – passwords are hashed, only needed info is collected |
| 4 | Login | `/login` – wrong credentials give a friendly message |
| 5 | Web security | werkzeug password hashing · parameterized SQL · Jinja auto-escaping (XSS) · Flask-WTF CSRF protection |
| 6 | Session management | Flask sessions, `login_required` / `admin_required`, logout clears the session |
| 7 | SMTP email | `mailer.py` (welcome email + order status emails) |
| 8 | Dashboard | `/dashboard` (customer view and admin view) |
| 9 | Profile management | `/profile` – name, email, contact, address, profile photo, password |
| 10 | CRUD | Menu items (with choices), promos, and orders (create / read / update status / delete) |
| 11 | Responsive UI | Bootstrap 5 grid, works on desktop and mobile |
| 12 | Form validation & error handling | `validators.py` (server) + `static/js/validate.js` and HTML5 (browser) + friendly error pages |
| 13 | OOP | `models.py`: `Database`, `BaseModel` → `User`, `MenuItem`, `Promo`, `Order` (encapsulated rules such as `Order.record_call()` and `Promo.discount_for()`) |

## 5. Validation rules
`validators.py` and `static/js/validate.js` use the rules from manolo_real: capitalized real-looking names, Gmail or agency/school
emails, fake-email blocking, real Philippine mobile prefixes (rejects 1234567 / 9999999 / 1212121 patterns), username and password
rules, and duplicate email/username checks. The same contact-number check is used when placing an order.

## 6. Project files
```
app.py            routes + security helpers        models.py     OOP classes and SQL
validators.py     server-side validation           mailer.py     SMTP emails
config.py         settings                         init_db.py    creates the database
database/         kaingo_db.sql                    templates/    pages (Bootstrap)
static/           css, js, logo, dish photos (img/menu), uploads           apache/       Apache forwarding file for XAMPP
docs/             CLIENT_ENGAGEMENT.md (fill in)   requirements.txt, start_kaingo.bat, xampp_setup.bat
```

## 7. Notes
- Bootstrap loads from the internet (CDN). For offline use, download `bootstrap.min.css` and `bootstrap.bundle.min.js` into `static/`
  and point `templates/base.html` to them.
- Menu prices are samples – edit them in Admin → Menu.
- Submission checklist: GitHub link, this README, `docs/CLIENT_ENGAGEMENT.md` (client details, interview notes, feedback, sign-off).
