from flask import Blueprint, render_template, flash, redirect, url_for, send_from_directory, current_app, request
from flask_login import login_required, current_user
from .forms import ShopItemsForm, ProductEditForm
from werkzeug.utils import secure_filename
from .models import Product, Order
from . import db
import os

admin = Blueprint('admin', __name__)

@admin.route('/media/<path:filename>')
def get_image(filename):
    media_root = current_app.config["PRODUCT_MEDIA"]
    return send_from_directory(media_root, filename)

@admin.route('/add_items', methods=['GET', 'POST'])
@login_required
def add_items():
    if current_user.id != 1:
        flash("Access denied.", "error")
        return redirect(url_for('views.shop'))

    form = ShopItemsForm()
    if form.validate_on_submit():
        product_name = form.product_name.data
        in_stock     = form.in_stock.data
        category     = form.category.data

        file = form.product_picture.data
        filename = secure_filename(file.filename)

        upload_dir = current_app.config["PRODUCT_MEDIA"]
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, filename))

        new_shop_item = Product(
            product_name=product_name,
            in_stock=in_stock,
            category=category,
            product_picture=filename,   # ✅ fixed typo
        )
        db.session.add(new_shop_item)
        db.session.commit()
        flash(f'{product_name} added successfully', 'success')
        return redirect(url_for('admin.shop_items'))

    return render_template('add_shop_items.html', form=form)

@admin.route('/shop_items', methods=['GET'])
@login_required
def shop_items():
    if current_user.id != 1:
        flash("Access denied.", "error")
        return redirect(url_for('views.shop'))
    items = Product.query.order_by(Product.date_added).all()
    # If your template is named 'shopitems.html', change the next line accordingly.
    return render_template('shop_items.html', items=items)

@admin.route('/edit-product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if current_user.id != 1:
        flash("Access denied.", "error")
        return redirect(url_for('views.shop'))

    item = Product.query.get_or_404(product_id)
    form = ProductEditForm()

    if request.method == 'GET':
        form.product_name.data = item.product_name
        form.in_stock.data     = item.in_stock
        form.category.data     = item.category

    if form.validate_on_submit():
        item.product_name = form.product_name.data
        item.in_stock     = form.in_stock.data
        item.category     = form.category.data

        if form.product_picture.data:  # optional replace
            file = form.product_picture.data
            filename = secure_filename(file.filename)
            upload_dir = current_app.config["PRODUCT_MEDIA"]
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, filename))
            item.product_picture = filename  # store filename

        db.session.commit()
        flash('Product updated.', 'success')
        return redirect(url_for('admin.shop_items'))

    return render_template('edit_product.html', form=form, item=item)

@admin.route('/delete-product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if current_user.id != 1:
        flash("Access denied.", "error")
        return redirect(url_for('views.shop'))

    item = Product.query.get_or_404(product_id)
    db.session.delete(item)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin.shop_items'))
    
@admin.route('/orders/all')
@login_required
def all_orders():
    if current_user.id != 1:
        flash("Not available", "error")
        return redirect(url_for('cart.order_history'))
    
    orders = Order.query.order_by(Order.submitted_at.desc()).all()
    return render_template('order_history.html', orders=orders, admin_view=True)
