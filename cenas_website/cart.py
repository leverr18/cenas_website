# cart.py
import csv
import io
import os
import smtplib
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from math import inf

from flask import (Blueprint, Response, abort, current_app, flash, jsonify, redirect, render_template, request, url_for)

from flask_login import current_user, login_required
from sqlalchemy import case

from . import db
from .models import Cart, Order, OrderItem, Product

cart = Blueprint('cart', __name__)

def _clamp(n, lo, hi):
    try:
        return max(lo, min(hi, n))
    except TypeError:
        # if hi is None, treat as infinite upper bound
        return max(lo, n)

def _get_line(product_id):
    return Cart.query.filter_by(customer_link=current_user.id, product_link=product_id).first()

def _store_from_email(email):
    email = (email or "").lower()
    if "tomball" in email:
        return "Tomball"
    if "copperfield" in email:
        return "Copperfield"
    if "corporate" in email:
        return "Corporate"
    return "Unknown"

def _is_ajax(req) -> bool:
    """Detect if the request came from JS (fetch/XHR) or explicitly asked for JSON."""
    hdr = (req.headers.get("X-Requested-With") or "").lower()
    return (
        hdr in ("fetch", "xmlhttprequest")
        or req.form.get("_ajax") == "1"
        or req.args.get("_ajax") == "1"
        or req.accept_mimetypes.best == "application/json"
    )

@cart.route('/orders')
@login_required
def order_history():
    orders = (Order.query.filter_by(customer_link=current_user.id).order_by(Order.submitted_at.desc()).all())
    return render_template('order_history.html', orders=orders, admin_view=False)

@cart.route('/orders/<int:order_id>/csv')
@login_required
def download_order_csv(order_id):
    order = Order.query.get_or_404(order_id)
    if order.customer_link != current_user.id and current_user.id != 1:
        abort(403)
    
    store = _store_from_email(order.customer.email)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Order #', 'Store', 'Employee', 'Category', 'Item', 'Quantity'])
    date_str = order.submitted_at.strftime('%Y-%m-%d %H:%M')
    for item in sorted(order.items, key=lambda x: (x.product_category, x.product_name)):
        writer.writerow([date_str, order.id, store, order.customer.username, item.product_category, item.product_name, item.quantity])

    filename = f'order_{order.id}_{order.submitted_at.strftime("%Y%m%d")}.csv'
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@cart.route('/orders/export-all')
@login_required
def export_all_orders_csv():
    if current_user.id != 1:
        abort(403)

    orders = Order.query.order_by(Order.submitted_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Order #', 'Store', 'Employee', 'Category', 'Item', 'Quantity'])
    for order in orders:
        store = _store_from_email(order.customer.email)
        date_str = order.submitted_at.strftime('%Y-%m-%d %H:%M')
        for item in sorted(order.items, key=lambda x: (x.product_category, x.product_name)):
            writer.writerow([date_str, order.id, store, order.customer.username, item.product_category, item.product_name, item.quantity])

    filename = f'all_orders_{datetime.now(timezone.utc).strftime("%Y%m%d")}.csv'
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

@cart.route('/cart')
@login_required
def view_cart():
    lines = Cart.query.filter_by(customer_link=current_user.id).all()
    total_items = sum(l.quantity for l in lines)
    return render_template('cart.html', lines=lines, total_items=total_items)

@cart.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_item(product_id):
    """Add/set a product quantity from the shop page.

    - AJAX (fetch/_ajax=1): SET the line to the exact qty (idempotent).
    - Non-AJAX: increment (legacy behavior).
    """
    is_ajax = _is_ajax(request)
    product = Product.query.get_or_404(product_id)

    # Parse quantity robustly
    try:
        qty = int(request.form.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    max_qty = product.in_stock if product.in_stock is not None else inf
    qty = _clamp(qty, 1, max_qty)

    line = _get_line(product.id)
    created = line is None
    if line:
        line.quantity = qty if is_ajax else _clamp(line.quantity + qty, 1, max_qty)
    else:
        line = Cart(quantity=qty, customer_link=current_user.id, product_link=product.id)
        db.session.add(line)

    db.session.commit()

    if is_ajax:
        # Return the actual saved quantity
        return jsonify({"ok": True, "product_id": product.id, "quantity": line.quantity, "created": created})

    flash('Added to cart.', 'success')
    return redirect(request.referrer or url_for('views.shop'))


@cart.route('/cart/update/<int:product_id>', methods=['POST'])
@login_required
def update_quantity(product_id):
    """Set quantity to an explicit value (typed in box or +/- result on the cart page)."""
    is_ajax = _is_ajax(request)
    product = Product.query.get_or_404(product_id)
    line = _get_line(product.id)
    if not line:
        if is_ajax:
            return jsonify({"ok": False, "error": "Item not in cart"}), 404
        flash('Item not in cart.', 'error')
        return redirect(url_for('cart.view_cart'))

    try:
        qty = int(request.form.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    if qty <= 0:
        db.session.delete(line)
        db.session.commit()
        if is_ajax:
            return jsonify({"ok": True, "removed": True})
        flash('Removed from cart.', 'info')
        return redirect(request.referrer or url_for('cart.view_cart'))

    max_qty = product.in_stock if product.in_stock is not None else inf
    line.quantity = _clamp(qty, 1, max_qty)
    db.session.commit()
    if is_ajax:
        return jsonify({"ok": True, "removed": False, "quantity": line.quantity})
    flash('Quantity updated.', 'success')
    return redirect(request.referrer or url_for('cart.view_cart'))

@cart.route('/cart/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_item(product_id):
    is_ajax = _is_ajax(request)
    product = Product.query.get_or_404(product_id)
    line = _get_line(product.id)
    if line:
        db.session.delete(line)
        db.session.commit()
    if is_ajax:
        return jsonify({"ok": True})
    flash('Removed from cart.', 'info')
    return redirect(request.referrer or url_for('cart.view_cart'))

@cart.route('/cart/submit', methods=['POST'])
@login_required
def submit_cart():
    lines = Cart.query.filter_by(customer_link=current_user.id).all()
    if not lines:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('cart.view_cart'))
    
    product_ids = [l.product_link for l in lines]
    products = {p.id: p for p in Product.query.filter(Product.id.in_(product_ids)).all()}

    # decrement stock (floor at 0)
    for l in lines:
        p = products.get(l.product_link)
        if p:
            Product.query.filter_by(id=p.id).update({"in_stock": case((Product.in_stock >= l.quantity, Product.in_stock - l.quantity), else_=0)}, synchronize_session="fetch")
    
    order = Order(status="Submitted", customer_link=current_user.id)
    db.session.add(order)
    db.session.flush()

    for l in lines:
        p = products.get(l.product_link)
        db.session.add(OrderItem(
            order_link=order.id,
            product_name=p.product_name if p else f"[Deleted Product #{l.product_link}]",
            product_category=p.category if p else "Unknown", quantity=l.quantity,
        ))
    
    for l in lines:
        db.session.delete(l)
    
    db.session.commit()

    # Send notification email (non-blocking - order is already persisted)
    try:
        _send_order_email(order)
    except Exception:
        current_app.logger.exception("Order #%s saved but email notification failed.", order.id)
        flash("Order submitted. Email notification failed - contact your manager.", "warning")
        return redirect(url_for('views.shop'))
    
    # Best effort cleanup of old orders
    try:
        _cleanup_old_orders()
    except Exception:
        current_app.logger.exception("Order retention cleanup failed (non-critical).")

    flash("Order submitted to Corporate.", "success")
    return redirect(url_for('views.shop'))
    
# --------- Helpers ---------

def _send_order_email(order: Order):
    grouped = defaultdict(list)
    for item in order.items:
        grouped[item.product_category].append(item)

    item_rows = ""
    for category in sorted(grouped):
        item_rows += f"""
        <tr>
        <td colspan="3" style="padding:10px; background:#f0f0f0; font-weight:bold;">
              {category.upper()}
            </td>
          </tr>"""
        for item in sorted(grouped[category], key=lambda x: x.product_name):
            item_rows += f"""
        <tr>
        <td style="padding:8px; border-bottom:1px solid #ddd;">&#9744;</td>
        <td style="padding:8px; border-bottom:1px solid #ddd;">{item.product_name}</td>
            <td style="padding:8px; border-bottom:1px solid #ddd; text-align:center;">{item.quantity}</td>
          </tr>"""

    total = sum(i.quantity for i in order.items)

    html_body = f"""
      <html><body style="font-family:Arial,sans-serif; background:#f4f4f4; padding:20px;">
        <div style="max-width:650px; margin:auto; background:#fff; padding:24px; border-radius:6px;">
          <h2 style="margin-top:0;">Corporate Order #{order.id}</h2>
          <p>
            <strong>Customer:</strong><br>
            {order.customer.username}<br>
            {order.customer.email}
          </p>
          <h3 style="margin-top:30px;">Order Checklist</h3>
          <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
            <thead>
              <tr>
                <th align="left" style="padding:8px; border-bottom:2px solid #333;">&#10004;</th>
                <th align="left" style="padding:8px; border-bottom:2px solid #333;">Item</th>
                <th align="center" style="padding:8px; border-bottom:2px solid #333;">Qty</th>
              </tr>
            </thead>
            <tbody>{item_rows}</tbody>
          </table>
          <p style="margin-top:20px;"><strong>Total items:</strong> {total}</p>
          <hr style="margin:30px 0;">
          <table width="100%">
            <tr>
              <td style="padding-top:20px;"><strong>Loaded
  by:</strong><br>___________________________</td>
              <td style="padding-top:20px;"><strong>Verified
  by:</strong><br>___________________________</td>
            </tr>
          </table>
          <p style="font-size:12px; color:#777; margin-top:30px;">
            Generated by the Cenas Kitchen corporate ordering system.
          </p>
        </div>
      </body></html>"""

    plain = (
          f"Order #{order.id} — {order.customer.username}({order.customer.email})\n\n"
          + "\n".join(f"- [{i.product_category}] {i.product_name} x {i.quantity}" for
   i in order.items)
      )

    recipients = [e.strip() for e in os.environ.get("ORDER_NOTIFICATION_EMAILS",
  "").split(",") if e.strip()]
    _send_email(
          subject=f"Corporate Order #{order.id} — {order.customer.username}",
          body=plain,
          html_body=html_body,
          to_email=recipients,
      )
    
def _send_email(subject: str, body: str, to_email, html_body: str = None):
    if not to_email:
        raise RuntimeError("No email recipients configured.")
    
    if isinstance(to_email, str):
        to_email = [to_email]

    host = os.environ["SMTP_HOST"]
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    from_email = os.environ.get("FROM_EMAIL", user)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = ", ".join(to_email)
    msg.set_content(body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(host, port) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    
def _cleanup_old_orders():
    retention_days = int(os.environ.get("ORDER_RETENTION_DAYS", 90))
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    old_orders = Order.query.filter(Order.submitted_at < cutoff).all()
    for o in old_orders:
        db.session.delete(o) # cascades to OrderItem
    if old_orders:
        db.session.commit()
        current_app.logger.info("Purged %d order(s) older than %d days.", len(old_orders), retention_days)