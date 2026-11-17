import os
import json
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, g
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.utils import secure_filename

from config import Config
from models import User, MenuItem, Promo, Order
import validators
from mailer import send_email

app = Flask(__name__)
app.config.from_object(Config)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")
csrf = CSRFProtect(app)          # Flask-WTF: every POST form must carry the hidden csrf_token field


# ---------------------------------------------------------------- security + session helpers
@app.context_processor
def inject_globals():
    return dict(current_user=current_user(), BRAND=Config.BRAND, RESTAURANT=Config.RESTAURANT_NAME,
                MAX_CALLS=Config.MAX_CALL_ATTEMPTS)


def current_user():
    if "user" not in g:
        g.user = User.find(session.get("user_id"))
    return g.user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user():
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user().is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def notify_customer(order, extra=""):
    """SMTP email to the customer whenever their order changes."""
    user = User.find(order.user_id)
    if user:
        send_email(user.email, f"{Config.BRAND} - Order #{order.id}: {order.label()}",
                   f"Hi {user.firstname},\n\nYour order #{order.id} is now: {order.label()}.\n{extra}\n"
                   f"Total: ₱{float(order.total):.2f} ({order.payment_method})\n\n"
                   f"Thank you for ordering from {Config.RESTAURANT_NAME}!")


# ---------------------------------------------------------------- public pages
@app.route("/")
def index():
    return render_template("index.html", promos=Promo.active_list())


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("dashboard"))
    form = {}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in ("firstname", "lastname", "email", "contact", "username")}
        form["password"] = request.form.get("password", "")
        form["confirm"] = request.form.get("confirm", "")
        errors = validators.validate_register(form)
        if not errors and User.exists("email", form["email"]):
            errors.append("Email already registered.")
        if not errors and User.exists("username", form["username"]):
            errors.append("Username already exists.")
        for e in errors:
            flash(e, "danger")
        if not errors:
            User.create(form)
            send_email(form["email"], f"Welcome to {Config.BRAND}!",
                       f"Hi {form['firstname']},\n\nYour account is ready. Log in and start ordering online!")
            flash("Registration successful! You can log in now.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user = User.find_by_email(email) if email else None
        if user and user.check_password(request.form.get("password", "")):
            session.clear()                      # new session after login
            session["user_id"] = user.id
            user.touch_login()
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html", email=email)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


# ---------------------------------------------------------------- customer pages
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    if user.is_admin:
        return render_template("dashboard.html", stats=Order.admin_stats(), pending=Order.with_customer("Pending Call"))
    return render_template("dashboard.html", stats=Order.user_stats(user.id), orders=Order.for_user(user.id)[:5],
                           promos=Promo.active_list())


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    if request.method == "POST":
        if request.form.get("action") == "details":
            f = {k: request.form.get(k, "").strip() for k in ("firstname", "lastname", "email", "contact", "address")}
            errors = [e for e in (validators.name_error(f["firstname"], "First Name"),
                                  validators.name_error(f["lastname"], "Last Name", True),
                                  validators.email_error(f["email"]),
                                  validators.contact_error(f["contact"])) if e]
            if not errors and User.exists("email", f["email"], user.id):
                errors.append("That email is already used by another account.")
            photo = request.files.get("photo")
            photo_name = None
            if photo and photo.filename:                       # optional profile photo
                ext = photo.filename.rsplit(".", 1)[-1].lower()
                if ext not in ("png", "jpg", "jpeg"):
                    errors.append("Profile photo must be a PNG or JPG image.")
                else:
                    photo_name = secure_filename(f"user{user.id}.{ext}")
            for e in errors:
                flash(e, "danger")
            if not errors:
                if photo_name:
                    photo.save(os.path.join(Config.UPLOAD_FOLDER, photo_name))
                user.update_profile(f["firstname"], f["lastname"], f["email"], f["contact"], f["address"], photo_name)
                flash("Profile updated.", "success")
        else:
            old, new, confirm = (request.form.get(k, "") for k in ("old", "new", "confirm"))
            error = validators.password_error(new, confirm)
            if not user.check_password(old):
                flash("Current password is incorrect.", "danger")
            elif error:
                flash(error, "danger")
            else:
                user.set_password(new)
                flash("Password changed.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)


# ---------------------------------------------------------------- ordering
def order_page(cart=None, form=None):
    return render_template("order.html", menu=MenuItem.available(), promos=Promo.active_list(),
                           cart=cart or [], form=form or {})


@app.route("/order")
@login_required
def order_now():
    if current_user().is_admin:
        return redirect(url_for("dashboard"))
    return order_page()


@app.route("/order/place", methods=["POST"])
@login_required
def place_order():
    user = current_user()
    # the order page sends the whole cart as JSON: [{"id": 1, "qty": 2, "picks": {"Drink": "Iced Tea"}}, ...]
    try:
        cart = json.loads(request.form.get("cart_json", "[]"))
        if not isinstance(cart, list):
            raise ValueError
    except ValueError:
        cart = []
    order_type = request.form.get("order_type", "")
    contact = request.form.get("contact", "").strip()
    address = request.form.get("address", "").strip()

    errors = []
    if order_type not in ("Delivery", "Pickup"):
        errors.append("Please choose Delivery or Pickup.")
    if validators.contact_error(contact):
        errors.append(validators.contact_error(contact))
    if order_type == "Delivery" and len(address) < 10:
        errors.append("Please enter your complete delivery address.")
    if not request.form.get("call_ok"):
        errors.append("Please agree to answer the confirmation call.")
    if not errors:
        try:
            order_id = Order.place(user.id, cart, order_type, contact, address, request.form.get("promo_code", "").strip())
        except ValueError as e:
            errors.append(str(e))
    if errors:
        for e in errors:
            flash(e, "danger")
        return order_page(cart, request.form)          # show the page again with what the customer chose

    notify_customer(Order.find(order_id), "The restaurant will call you soon to confirm your order. Please keep your phone line open.")
    flash(f"Order #{order_id} placed! The restaurant will call {contact} to confirm it.", "success")
    return redirect(url_for("order_detail", order_id=order_id))


@app.route("/orders")
@login_required
def my_orders():
    return render_template("orders.html", orders=Order.for_user(current_user().id))


def get_order_or_404(order_id):
    order = Order.find(order_id)
    if not order or (order.user_id != current_user().id and not current_user().is_admin):
        abort(404)
    return order


@app.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = get_order_or_404(order_id)
    return render_template("order_detail.html", order=order, items=order.items(), logs=order.logs(),
                           customer=User.find(order.user_id))


@app.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    order = get_order_or_404(order_id)
    if order.status == "Pending Call" and order.user_id == current_user().id:
        order.cancel("Cancelled by customer")
        flash("Order cancelled.", "info")
    else:
        flash("This order can no longer be cancelled online. Please call the restaurant.", "warning")
    return redirect(url_for("order_detail", order_id=order_id))


# ---------------------------------------------------------------- admin: orders
@app.route("/admin/orders")
@admin_required
def admin_orders():
    status = request.args.get("status", "")
    if status not in Order.FLOW + ["Cancelled"]:
        status = ""
    return render_template("admin_orders.html", orders=Order.with_customer(status or None),
                           statuses=Order.FLOW + ["Cancelled"], selected=status)


@app.route("/admin/orders/<int:order_id>/action", methods=["POST"])
@admin_required
def order_action(order_id):
    order = Order.find(order_id) or abort(404)
    action = request.form.get("action")
    if action in ("confirmed", "no_answer", "declined"):
        order.record_call(action)                       # result of the confirmation call
    elif action == "next":
        order.advance()
    elif action == "cancel":
        order.cancel("Cancelled by staff")
    elif action == "delete" and order.is_closed:
        Order.remove(order.id)
        flash(f"Order #{order_id} deleted.", "info")
        return redirect(url_for("admin_orders"))
    else:
        abort(400)
    order = Order.find(order_id)
    flash(f"Order #{order.id} is now: {order.label()}.", "success")
    notify_customer(order)
    return redirect(url_for("admin_orders", status=request.form.get("filter") or None))


# ---------------------------------------------------------------- admin: menu (CRUD)
@app.route("/admin/menu", methods=["GET", "POST"])
@admin_required
def admin_menu():
    item_id = request.values.get("id", type=int)         # set when editing
    item = MenuItem.find(item_id) if item_id else None
    form = item.__dict__ if item else {"emoji": "🍽️", "available": 1}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in ("name", "category", "emoji", "description", "choices")}
        form["available"] = request.form.get("available")
        errors = []
        if not form["name"] or not form["category"]:
            errors.append("Name and category are required.")
        if form["choices"] and not MenuItem.parse_choices(form["choices"]):
            errors.append("Choices must look like  Main:Pares|Mami;Drink:Iced Tea|Softdrink")
        try:
            form["price"] = round(float(request.form.get("price", "")), 2)
            if form["price"] <= 0:
                raise ValueError
        except ValueError:
            errors.append("Price must be a number greater than 0.")
        photo = request.files.get("image")
        ext = photo.filename.rsplit(".", 1)[-1].lower() if photo and photo.filename else ""
        if ext and ext not in ("png", "jpg", "jpeg", "webp"):
            errors.append("The dish photo must be a PNG, JPG or WEBP image.")
        for e in errors:
            flash(e, "danger")
        if not errors:
            saved_id = MenuItem.save(form, item_id)
            if ext:                                              # optional dish photo
                filename = secure_filename(f"item-{saved_id}.{ext}")
                photo.save(os.path.join(Config.MENU_IMAGE_FOLDER, filename))
                MenuItem.set_image(saved_id, filename)
            flash("Menu item saved.", "success")
            return redirect(url_for("admin_menu"))
    return render_template("admin_menu.html", items=MenuItem.all(), form=form, editing=item_id)


@app.route("/admin/menu/<int:item_id>/delete", methods=["POST"])
@admin_required
def menu_delete(item_id):
    MenuItem.delete(item_id)
    flash("Menu item deleted.", "info")
    return redirect(url_for("admin_menu"))


# ---------------------------------------------------------------- admin: promos (CRUD)
@app.route("/admin/promos", methods=["GET", "POST"])
@admin_required
def admin_promos():
    promo_id = request.values.get("id", type=int)
    promo = Promo.find(promo_id) if promo_id else None
    form = promo.__dict__ if promo else {"discount_type": "percent", "min_spend": 0, "active": 1}
    if request.method == "POST":
        form = {k: request.form.get(k, "").strip() for k in
                ("code", "title", "description", "discount_type", "start_date", "end_date")}
        form["code"] = form["code"].upper()
        form["active"] = request.form.get("active")
        errors = []
        if not form["code"].isalnum() or not 3 <= len(form["code"]) <= 20:
            errors.append("Promo code must be 3-20 letters or numbers.")
        if not form["title"]:
            errors.append("Title is required.")
        try:
            form["discount_value"] = float(request.form.get("discount_value", ""))
            form["min_spend"] = float(request.form.get("min_spend") or 0)
            if form["discount_value"] <= 0 or form["min_spend"] < 0 or (
                    form["discount_type"] == "percent" and form["discount_value"] > 100):
                raise ValueError
        except ValueError:
            errors.append("Discount value / minimum spend are not valid numbers.")
        if form["discount_type"] not in ("percent", "fixed"):
            errors.append("Choose percent or fixed discount.")
        if form["start_date"] and form["end_date"] and form["end_date"] < form["start_date"]:
            errors.append("End date cannot be before the start date.")
        if not errors:
            try:
                Promo.save(form, promo_id)
                flash("Promo saved.", "success")
                return redirect(url_for("admin_promos"))
            except Exception:
                errors.append("That promo code already exists.")
        for e in errors:
            flash(e, "danger")
    return render_template("admin_promos.html", promos=Promo.all(), form=form, editing=promo_id)


@app.route("/admin/promos/<int:promo_id>/delete", methods=["POST"])
@admin_required
def promo_delete(promo_id):
    Promo.delete(promo_id)
    flash("Promo deleted.", "info")
    return redirect(url_for("admin_promos"))


# ---------------------------------------------------------------- friendly error pages
@app.errorhandler(CSRFError)
@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, message="Your session expired or the form was invalid. Please go back and try again."), 400


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="You are not allowed to open this page."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="We could not find that page."), 404


@app.errorhandler(413)
def too_large(e):
    return render_template("error.html", code=413, message="That file is too large (maximum 2 MB)."), 413


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Something went wrong on our side. Please try again."), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)       # local hosting: http://127.0.0.1:5000
