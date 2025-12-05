from flask import Flask, render_template, jsonify
import json
import os

app = Flask(__name__)

# Load the scientist network data
def load_network_data():
    """Load the scientist network data from JSON file"""
    try:
        with open('scientist_network_final.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": "Network data file not found"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON data"}
    except Exception as e:
        return {"error": f"Error loading data: {str(e)}"}

@app.route('/')
def index():
    """Serve the main visualization page"""
    return render_template('visualization.html')

@app.route('/data')
def get_network_data():
    """API endpoint to serve the scientist network data"""
    data = load_network_data()
    return jsonify(data)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Scientist Network API is running"})

if __name__ == '__main__':
    # Check if data file exists
    if not os.path.exists('scientist_network_final.json'):
        print("Warning: scientist_network_final.json not found!")
        print("Make sure the data file is in the same directory as app.py")
    
    # Run the Flask app
    print("Starting Scientist Network Visualization Server...")
    print("Open your browser and go to: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5020) 