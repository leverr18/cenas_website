from flask import Blueprint, render_template, jsonify, request
from cenas_website import dictionaries
from flask_login import login_required, current_user
from .models import Product, Order, Cart

locations = dictionaries.locations
menu_items = dictionaries.menu_items
weekly_specials = dictionaries.weekly_specials
vegetarian_items = dictionaries.vegetarian_items
drink_items = dictionaries.drink_items
coffee_items = dictionaries.coffee_items

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('home.html')

@views.route("/about-us")
def about_us():
    return render_template("about.html", locations=locations)

@views.route('/locations')
def get_locations():
    return jsonify(locations)

@views.route('/career')
def career():
    return render_template("career.html")

@views.route('/catering')
def catering():
    return render_template("catering.html")

@views.route('/cateringmenu')
def cateringmenu():
    return render_template("catering-menu.html")

@views.route('/community')
def community():
    return render_template("community.html")

@views.route('/donations')
def donations():
    return render_template("communitydonations.html")

@views.route('/contact')
def contact():
    return render_template("contact.html")

@views.route('/weekly_specials_data')
def weekly_specials_data():
    return jsonify(weekly_specials)

@views.route('/menu')
def menu():
    return render_template("menu.html", menu_items=menu_items, weekly_specials=weekly_specials)

@views.route('/menu_data')
def menu_data():
    return jsonify(menu_items)

@views.route('/veggie_menu_data')
def vegetarian_menu_data():
    return jsonify(vegetarian_items)

@views.route('/vegetarian_menu')
def vegetarian_menu():
    return render_template("vegetarian_menu.html", vegetarian_items=vegetarian_items)

@views.route('/gallery')
def gallery():
    return render_template("gallery.html")

@views.route('/drinks')
def drinks():
    return render_template("drinkmenu.html", drink_items=drink_items, weekly_specials=weekly_specials)

@views.route("/coffee")
def coffee_menu():
    return render_template("coffee.html", coffee_items=coffee_items)

@views.route('/drink_data')
def drink_data():
    return jsonify(drink_items)

@views.route('/orderlocation')
def orderlocation():
    return render_template("chooselocation.html", locations=locations)

@views.route('/thank-you')
def thank_you():
    return render_template("thank_you.html")

@views.route('/dashboard')
@login_required
def dashboard():
    recent_orders = (Order.query
                     .filter_by(customer_link=current_user.id)
                     .order_by(Order.submitted_at.desc())
                     .limit(3).all())
    return render_template('dashboard.html', recent_orders=recent_orders)

@views.route('/shop')
@login_required
def shop():
    products = Product.query.order_by(Product.category, Product.product_name).all()

    grouped = {}
    for p in products:
        grouped.setdefault(p.category, []).append(p)

    categories = sorted(grouped.keys())
    cart_qtys = {c.product_link: c.quantity
                 for c in Cart.query.filter_by(customer_link=current_user.id).all()}
    return render_template("shop.html", grouped=grouped, categories=categories, cart_qtys=cart_qtys)

