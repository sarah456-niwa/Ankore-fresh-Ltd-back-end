import requests
from decimal import Decimal
from django.conf import settings

def process_payment(order, payment_method, payment_data=None):
    """Process payment based on method"""
    
    if payment_method == 'momo':
        return process_mtn_momo_payment(order, payment_data)
    elif payment_method == 'airtel':
        return process_airtel_money_payment(order, payment_data)
    elif payment_method == 'card':
        return process_card_payment(order, payment_data)
    else:
        return {'success': False, 'error': 'Invalid payment method'}

def process_mtn_momo_payment(order, payment_data):
    """Process MTN Mobile Money payment"""
    try:
        # In production, integrate with MTN MoMo API
        # For now, return mock success
        return {
            'success': True, 
            'transaction_id': f'MOMO-{order.order_number}',
            'message': 'Payment initiated successfully'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def process_airtel_money_payment(order, payment_data):
    """Process Airtel Money payment"""
    try:
        # In production, integrate with Airtel Money API
        return {
            'success': True,
            'transaction_id': f'AIRTEL-{order.order_number}',
            'message': 'Payment initiated successfully'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def process_card_payment(order, payment_data):
    """Process Credit/Debit Card payment"""
    try:
        # Integrate with Stripe or other payment gateway
        return {
            'success': True,
            'transaction_id': f'CARD-{order.order_number}',
            'message': 'Payment processed successfully'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}