from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model
from products.models import Product
from cart.models import CartItem
from .models import Order, OrderItem
import logging
log = logging.getLogger('orders')
User = get_user_model()
class InsufficientStock(Exception): pass
class InsufficientBalance(Exception): pass
@transaction.atomic
def create_order_from_cart(user: User) -> Order:
    items = list(CartItem.objects.select_related('product').select_for_update().filter(user=user))
    if not items:
        raise ValueError("Cart is empty.")
    total = Decimal('0.00')
    for item in items:
        if item.quantity > item.product.stock:
            raise InsufficientStock(f"Not enough stock for {item.product.name}")
        total += item.product.price * item.quantity
    user.refresh_from_db()
    if user.balance < total:
        raise InsufficientBalance("Insufficient balance.")
    user.balance -= total; user.save(update_fields=['balance'])
    for item in items:
        p = item.product; p.stock -= item.quantity; p.save(update_fields=['stock'])
    order = Order.objects.create(user=user, total=total, status='created')
    OrderItem.objects.bulk_create([OrderItem(order=order, product=i.product, price=i.product.price, quantity=i.quantity) for i in items])
    CartItem.objects.filter(user=user).delete()
    log.info("Order %s created for user %s with total %s", order.id, user.username, total)
    return order
