"""Database + model classes (OOP): BaseModel -> User, MenuItem, Promo, Order."""
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config


class Database:
    """Small wrapper around MySQL. Every query is parameterized (%s) to stop SQL injection."""

    def connect(self):
        import mysql.connector
        return mysql.connector.connect(host=Config.DB_HOST, user=Config.DB_USER, password=Config.DB_PASSWORD,
                                       database=Config.DB_NAME, charset="utf8mb4")

    def fetch_all(self, sql, params=()):
        conn = self.connect()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

    def fetch_one(self, sql, params=()):
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    def execute(self, sql, params=()):
        conn = self.connect()
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()
            conn.close()


db = Database()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class BaseModel:
    """Parent class: a database row becomes an object whose columns are attributes."""
    table = ""
    order_by = "id DESC"

    def __init__(self, row):
        self.__dict__.update(row)

    @classmethod
    def wrap(cls, row):
        return cls(row) if row else None

    @classmethod
    def all(cls):
        return [cls(r) for r in db.fetch_all(f"SELECT * FROM {cls.table} ORDER BY {cls.order_by}")]

    @classmethod
    def find(cls, row_id):
        if not row_id:
            return None
        return cls.wrap(db.fetch_one(f"SELECT * FROM {cls.table} WHERE id=%s", (row_id,)))

    @classmethod
    def delete(cls, row_id):
        db.execute(f"DELETE FROM {cls.table} WHERE id=%s", (row_id,))


class User(BaseModel):
    table = "users"

    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"

    @property
    def is_admin(self):
        return self.role == "admin"

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def find_by_email(cls, email):
        return cls.wrap(db.fetch_one("SELECT * FROM users WHERE LOWER(email)=%s", (email.lower(),)))

    @classmethod
    def exists(cls, field, value, exclude_id=0):
        if field not in ("email", "username"):
            raise ValueError("bad field")
        return db.fetch_one(f"SELECT id FROM users WHERE LOWER({field})=%s AND id<>%s", (value.lower(), exclude_id)) is not None

    @classmethod
    def create(cls, f):
        return db.execute(
            "INSERT INTO users (firstname, lastname, email, contact, username, password_hash, created_at) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (f["firstname"], f["lastname"], f["email"], f["contact"], f["username"],
             generate_password_hash(f["password"]), now()))

    def touch_login(self):
        db.execute("UPDATE users SET last_login=%s WHERE id=%s", (now(), self.id))

    def update_profile(self, firstname, lastname, email, contact, address, photo=None):
        db.execute("UPDATE users SET firstname=%s, lastname=%s, email=%s, contact=%s, address=%s WHERE id=%s",
                   (firstname, lastname, email, contact, address, self.id))
        if photo:
            db.execute("UPDATE users SET photo=%s WHERE id=%s", (photo, self.id))

    def set_password(self, new_password):
        db.execute("UPDATE users SET password_hash=%s WHERE id=%s", (generate_password_hash(new_password), self.id))


class MenuItem(BaseModel):
    table = "menu_items"
    order_by = "category, name"

    @staticmethod
    def parse_choices(text):
        """'Main:Pares|Mami;Drink:Iced Tea|Softdrink' -> [{'name': 'Main', 'options': ['Pares', 'Mami']}, ...]"""
        groups = []
        for part in (text or "").split(";"):
            if ":" in part:
                name, options = part.split(":", 1)
                options = [o.strip() for o in options.split("|") if o.strip()]
                if name.strip() and options:
                    groups.append({"name": name.strip(), "options": options})
        return groups

    @classmethod
    def available(cls):
        rows = db.fetch_all("SELECT * FROM menu_items WHERE available=1 ORDER BY id")      # same order as the restaurant's board
        return [{"id": r["id"], "name": r["name"], "category": r["category"], "price": float(r["price"]),
                 "emoji": r["emoji"], "image": r["image"] or "", "description": r["description"],
                 "groups": cls.parse_choices(r["choices"])}
                for r in rows]

    @classmethod
    def save(cls, f, item_id=None):
        """Adds or updates a food. Returns its id (the photo is saved separately with set_image)."""
        vals = (f["name"], f["category"], f["price"], f["emoji"], f["description"], f["choices"], 1 if f.get("available") else 0)
        if item_id:
            db.execute("UPDATE menu_items SET name=%s, category=%s, price=%s, emoji=%s, description=%s, choices=%s, "
                       "available=%s WHERE id=%s", vals + (item_id,))
            return item_id
        return db.execute("INSERT INTO menu_items (name, category, price, emoji, description, choices, available) "
                          "VALUES (%s,%s,%s,%s,%s,%s,%s)", vals)

    @classmethod
    def set_image(cls, item_id, filename):
        db.execute("UPDATE menu_items SET image=%s WHERE id=%s", (filename, item_id))


class Promo(BaseModel):
    table = "promos"

    def is_running(self):
        today = str(date.today())
        return (self.active == 1 and (not self.start_date or str(self.start_date) <= today)
                and (not self.end_date or today <= str(self.end_date)))

    def discount_for(self, subtotal):
        if self.discount_type == "percent":
            return round(subtotal * float(self.discount_value) / 100, 2)
        return min(float(self.discount_value), subtotal)

    @classmethod
    def active_list(cls):
        return [p for p in cls.all() if p.is_running()]

    @classmethod
    def check(cls, code, subtotal):
        """Returns (promo, error_message)."""
        promo = cls.wrap(db.fetch_one("SELECT * FROM promos WHERE UPPER(code)=%s", (code.strip().upper(),)))
        if not promo or not promo.is_running():
            return None, "That promo code is not valid."
        if subtotal < float(promo.min_spend):
            return None, f"Minimum spend for this promo is ₱{float(promo.min_spend):.0f}."
        return promo, None

    @classmethod
    def save(cls, f, promo_id=None):
        vals = (f["code"], f["title"], f["description"], f["discount_type"], f["discount_value"],
                f["min_spend"], f["start_date"] or None, f["end_date"] or None, 1 if f.get("active") else 0)
        if promo_id:
            db.execute("UPDATE promos SET code=%s, title=%s, description=%s, discount_type=%s, discount_value=%s, "
                       "min_spend=%s, start_date=%s, end_date=%s, active=%s WHERE id=%s", vals + (promo_id,))
        else:
            db.execute("INSERT INTO promos (code, title, description, discount_type, discount_value, min_spend, "
                       "start_date, end_date, active) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", vals)


class Order(BaseModel):
    table = "orders"
    FLOW = ["Pending Call", "Confirmed", "Preparing", "On the Way", "Completed"]
    # Pickup orders use slightly different words for the last two steps
    LABELS = {"Delivery": {"On the Way": "Out for Delivery", "Completed": "Delivered"},
              "Pickup": {"On the Way": "Ready for Pickup", "Completed": "Picked Up"}}

    def label(self, status=None):
        status = status or self.status
        return self.LABELS.get(self.order_type, {}).get(status, status)

    def steps(self):
        return [self.label(s) for s in self.FLOW]

    def step_index(self):
        return self.FLOW.index(self.status) if self.status in self.FLOW else -1

    @property
    def is_closed(self):
        return self.status in ("Completed", "Cancelled")

    def next_status(self):
        i = self.step_index()
        # "Pending Call" only moves forward through the confirmation call
        if self.status == "Pending Call" or i < 0 or i + 1 >= len(self.FLOW):
            return None
        return self.FLOW[i + 1]

    def items(self):
        return db.fetch_all("SELECT * FROM order_items WHERE order_id=%s", (self.id,))

    def logs(self):
        return db.fetch_all("SELECT * FROM status_logs WHERE order_id=%s ORDER BY id", (self.id,))

    # ---- updates ----
    def add_log(self, status, note):
        db.execute("INSERT INTO status_logs (order_id, status, note, created_at) VALUES (%s,%s,%s,%s)",
                   (self.id, status, note, now()))

    def set_status(self, status, note=""):
        db.execute("UPDATE orders SET status=%s WHERE id=%s", (status, self.id))
        self.add_log(status, note)
        self.status = status

    def record_call(self, result):
        """The restaurant calls the customer. result: confirmed / no_answer / declined."""
        if self.status != "Pending Call":
            return
        if result == "confirmed":
            db.execute("UPDATE orders SET call_status=%s WHERE id=%s", ("Confirmed", self.id))
            self.set_status("Confirmed", "Customer confirmed by phone call")
        elif result == "declined":
            db.execute("UPDATE orders SET call_status=%s WHERE id=%s", ("Declined", self.id))
            self.set_status("Cancelled", "Customer declined during the confirmation call")
        elif result == "no_answer":
            attempts = self.call_attempts + 1
            db.execute("UPDATE orders SET call_status=%s, call_attempts=%s WHERE id=%s", ("No Answer", attempts, self.id))
            self.call_attempts = attempts
            if attempts >= Config.MAX_CALL_ATTEMPTS:
                self.set_status("Cancelled", f"No answer after {attempts} call attempts")
            else:
                self.add_log("Pending Call", f"No answer (attempt {attempts})")

    def advance(self):
        nxt = self.next_status()
        if nxt:
            self.set_status(nxt, "Updated by staff")

    def cancel(self, note):
        if not self.is_closed:
            self.set_status("Cancelled", note)

    @classmethod
    def remove(cls, order_id):
        for table in ("order_items", "status_logs"):
            db.execute(f"DELETE FROM {table} WHERE order_id=%s", (order_id,))
        cls.delete(order_id)

    # ---- queries ----
    @classmethod
    def for_user(cls, user_id):
        return [cls(r) for r in db.fetch_all("SELECT * FROM orders WHERE user_id=%s ORDER BY id DESC", (user_id,))]

    @classmethod
    def with_customer(cls, status=None):
        sql = "SELECT o.*, u.firstname, u.lastname FROM orders o JOIN users u ON u.id=o.user_id"
        params = ()
        if status:
            sql += " WHERE o.status=%s"
            params = (status,)
        return [cls(r) for r in db.fetch_all(sql + " ORDER BY o.id DESC", params)]

    @classmethod
    def place(cls, user_id, cart, order_type, contact, address, promo_code):
        """Builds an order from the order form. Prices always come from the database, never the browser."""
        lines, subtotal = [], 0.0
        for entry in cart:
            try:
                item = MenuItem.find(int(entry["id"]))
                qty = int(entry["qty"])
                picks = entry.get("picks") or {}
            except (KeyError, TypeError, ValueError, AttributeError):
                raise ValueError("Your order has an invalid item.")
            if not item or not item.available or not 1 <= qty <= 20 or not isinstance(picks, dict):
                raise ValueError("An item in your order is not available.")
            notes = []                                   # the customer's choices, checked against the menu
            for group in MenuItem.parse_choices(item.choices):
                if picks.get(group["name"]) not in group["options"]:
                    raise ValueError(f"Please choose {group['name']} for {item.name}.")
                notes.append(f"{group['name']}: {picks[group['name']]}")
            lines.append((item, qty, "; ".join(notes)))
            subtotal += float(item.price) * qty
        if not lines:
            raise ValueError("Please tap at least one food to add it to your order.")

        discount, code = 0.0, None
        if promo_code:
            promo, err = Promo.check(promo_code, subtotal)
            if err:
                raise ValueError(err)
            discount, code = promo.discount_for(subtotal), promo.code

        order_id = db.execute(
            "INSERT INTO orders (user_id, order_type, payment_method, contact, address, subtotal, discount, total, "
            "promo_code, status, call_status, call_attempts, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (user_id, order_type, "COD" if order_type == "Delivery" else "Cash", contact,
             address if order_type == "Delivery" else "", subtotal, discount, round(subtotal - discount, 2), code,
             "Pending Call", "Pending", 0, now()))
        for item, qty, note in lines:
            db.execute("INSERT INTO order_items (order_id, item_id, name, price, qty, note) VALUES (%s,%s,%s,%s,%s,%s)",
                       (order_id, item.id, item.name, item.price, qty, note))
        cls.find(order_id).add_log("Pending Call", "Order placed - waiting for confirmation call")
        return order_id

    @classmethod
    def user_stats(cls, user_id):
        total = db.fetch_one("SELECT COUNT(*) AS n FROM orders WHERE user_id=%s", (user_id,))["n"]
        active = db.fetch_one("SELECT COUNT(*) AS n FROM orders WHERE user_id=%s AND status IN "
                              "('Pending Call','Confirmed','Preparing','On the Way')", (user_id,))["n"]
        return {"total": total, "active": active}

    @classmethod
    def admin_stats(cls):
        count = lambda sql, p=(): db.fetch_one(sql, p)["n"]
        return {
            "pending_calls": count("SELECT COUNT(*) AS n FROM orders WHERE status='Pending Call'"),
            "active": count("SELECT COUNT(*) AS n FROM orders WHERE status IN ('Confirmed','Preparing','On the Way')"),
            "today": count("SELECT COUNT(*) AS n FROM orders WHERE DATE(created_at)=%s", (str(date.today()),)),
        }
