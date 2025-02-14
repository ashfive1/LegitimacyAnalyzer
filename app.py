from flask import Flask, render_template, request, jsonify, send_file, url_for
import json
import os
import csv
import qrcode
from blockchain import Blockchain
from ai_model import predict_legitimacy

app = Flask(__name__)
blockchain = Blockchain()
DATA_FILE = os.path.join('data', 'blockchain_data.json')
CSV_FILE = os.path.join('data', 'block_inputs.csv')
QR_FOLDER = os.path.join('static', 'qr_codes')

# Ensure necessary directories exist
os.makedirs('data', exist_ok=True)
os.makedirs(QR_FOLDER, exist_ok=True)

# Load blockchain data from JSON file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

# Save blockchain data to JSON file
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump([block.to_dict() for block in blockchain.chain], f, indent=4)

# Save block inputs to CSV file
def save_to_csv(data):
    try:
        file_exists = os.path.exists(CSV_FILE)
        required_keys = ["productId", "checkpoint", "dateReceival", "dateShipping", "manager", "notes", "legitimacyScore"]

        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(required_keys)  # Add headers only if file doesn't exist

            writer.writerow([
                data['productId'],
                data['checkpoint'],
                data['dateReceival'],
                data['dateShipping'],
                data['manager'],
                data['notes'],
                data['legitimacyScore']
            ])

    except Exception as e:
        print(f"Error writing to CSV: {e}")

# Search for a product in CSV
def search_product_in_csv(product_id):
    try:
        with open(CSV_FILE, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            data = [row for row in reader if row and row[0].strip() == str(product_id)]
            if data:
                return data  # Return all entries for that product
        return None
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return None

# Generate QR Code
def generate_qr_code(product_id):
    qr_path = os.path.join(QR_FOLDER, f"{product_id}.png")

    if not os.path.exists(qr_path):  # Generate only if it doesn't exist
        qr = qrcode.make(f"http://127.0.0.1:5000/product/{product_id}")
        qr.save(qr_path)

    return qr_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_block', methods=['POST'])
def add_block():
    data = request.json
    notes = data.get("notes", "")  
    legitimacy_score = predict_legitimacy(str(notes))  

    new_block = {
        "productId": data["productId"],
        "checkpoint": data["checkpoint"],
        "dateReceival": data["dateReceival"],
        "dateShipping": data["dateShipping"],
        "manager": data["manager"],
        "notes": data["notes"],
        "legitimacyScore": legitimacy_score
    }

    blockchain.add_block(new_block)
    save_to_csv(new_block)  
    save_data()

    qr_path = generate_qr_code(data["productId"])  # Generate QR code

    return jsonify({"message": "Block added", "legitimacyScore": legitimacy_score, "qrCode": url_for('static', filename=f'qr_codes/{data["productId"]}.png')})

@app.route('/verify_product', methods=['POST'])
def verify_product():
    product_id = request.json.get("productId")
    product_data = search_product_in_csv(product_id)

    if not product_data:
        return jsonify({"error": "Product not found"}), 404

    legitimacy_scores = [float(row[6]) for row in product_data]
    avg_legitimacy_score = sum(legitimacy_scores) / len(legitimacy_scores)

    return jsonify({
        "productId": product_id,
        "averageLegitimacyScore": round(avg_legitimacy_score, 2),
        "qrCode": url_for('static', filename=f'qr_codes/{product_id}.png')
    }), 200

@app.route('/product/<product_id>')
def product_history(product_id):
    product_data = search_product_in_csv(product_id)
    if not product_data:
        return "Product not found", 404
    return jsonify(product_data)

@app.route('/get_chain')
def get_chain():
    return render_template('blockchain.html')

@app.route('/api/get_chain')
def api_get_chain():
    response = {"chain": blockchain.chain}
    return jsonify(response)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render provides a PORT env variable
    app.run(host="0.0.0.0", port=port)