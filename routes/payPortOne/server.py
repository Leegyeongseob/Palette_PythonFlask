import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:slrlal0510!@localhost/palette_springboot'
db = SQLAlchemy(app)

PORTONE_API_SECRET = 'JJb39tlTY10Gc1tIdjTmJe6mxUh3wYoNChE13mpG5U87gUcwCneLJ7UswDRRdFrklBibjkQ6ujs2opgq'

logging.basicConfig(level=logging.DEBUG)

@app.route('/payment/complete', methods=['POST'])
def payment_complete():
    data = request.json
    payment_id = data.get('paymentId')
    order_name = data.get('orderName')
    jwt_token = request.headers.get('Authorization')

    if not jwt_token:
        return jsonify({'error': 'Authorization token is missing'}), 401

    try:
        headers = {'Authorization': f'PortOne {PORTONE_API_SECRET}'}
        payment_response = requests.get(f'https://api.portone.io/payments/{payment_id}', headers=headers)

        logging.debug(f"PortOne API response status: {payment_response.status_code}")
        logging.debug(f"PortOne API response data: {payment_response.json()}")

        if payment_response.status_code != 200:
            return jsonify({'error': 'Payment verification failed'}), 400

        payment = payment_response.json()

        if 'amount' not in payment or 'customer' not in payment:
            return jsonify({'error': 'Payment response format error'}), 400

        order = {'amount': 1000}  # 예시용 데이터
        if order['amount'] == payment['amount']['total']:
            if payment['status'] == 'PAID':
                customer = payment.get('customer', {})
                fullName = customer.get('name', 'Unknown')
                phoneNumber = customer.get('phoneNumber', 'Unknown')
                email = customer.get('email', 'Unknown')

                payment_data = {
                    'paymentId': payment_id,
                    'orderName': order_name,
                    'totalAmount': payment['amount']['total'],
                    'customerName': fullName,
                    'customerPhone': phoneNumber,
                    'customerEmail': email,
                    'status': payment['status']
                }

                logging.debug(f"Sending payment data to Spring Boot server: {payment_data}")

                headers = {'Authorization': jwt_token}
                response = requests.post('http://localhost:8111/payment/complete', json=payment_data, headers=headers)
                logging.debug(f"Spring Boot server response: {response.status_code} - {response.text}")
                if response.status_code == 200:
                    return jsonify({'status': 'success'})
                else:
                    return jsonify({'error': 'Failed to save payment data to database'}), 500
            else:
                return jsonify({'error': 'Payment not completed'}), 400
        else:
            return jsonify({'error': 'Payment amount mismatch'}), 400

    except Exception as e:
        logging.error(f"Exception: {str(e)}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(port=5000)
