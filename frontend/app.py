from flask import Flask, render_template, render_template_string, url_for
import os

app = Flask(__name__)

# LOCAL
# BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5001")
# CON DOCKER COMPOSE
# BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5001")
# PARA INGRESS K8S
BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    raise RuntimeError("BACKEND_URL no configurado")

# TEMPLATE = """

# """

# @app.get("/")
# def index():
#     return render_template_string(TEMPLATE, backend=BACKEND_URL)

# @app.get("/")
# def index():
#     logo_url = url_for('static', filename='imgs/LogoSIMV.png')
#     return render_template_string(TEMPLATE, backend=BACKEND_URL, logo_url=logo_url)

@app.get("/")
def index():
    logo_url = url_for('static', filename='imgs/LogoSIMV.png')
    return render_template("index.html", backend=BACKEND_URL, logo_url=logo_url)

@app.route('/privacidad')
def privacidad():
    return render_template('privacidad.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)



