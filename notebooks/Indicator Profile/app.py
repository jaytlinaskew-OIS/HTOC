
import os
from flask import Flask, render_template, jsonify

# Determine absolute paths
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates')
STATIC_DIR    = os.path.join(ROOT_DIR, 'static')

# Initialize Flask with explicit absolute folders
app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
    static_url_path='/static'
)

# Debug print
print(f"→ ROOT_DIR:      {ROOT_DIR}")
print(f"→ Templates path: {app.template_folder}")
print(f"→ Loader search: {app.jinja_loader.searchpath}")
print(f"→ Files in templates: {os.listdir(TEMPLATES_DIR)}")

@app.route('/')
def home():
    return render_template('Profile_UI.html')

@app.route('/dictionary')
def dictionary():
    return render_template('Dictionary.html')

@app.route('/indicators')
def indicators_api():
    data = [{"Indicator": "104.21.48.1", "Frequency (7d)": 5, "Probability 7-Day": 80}]
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

