from flask import Flask
from flask_triangle import Triangle
from ActiveAMT.ActiveAMT_FLASK.Users import UserDbHandler
import os

app = Flask(__name__)
Triangle(app)

server_location = "https://127.0.0.1:5000/"

template_map = {
    'txt': 'text_hit.html',
    'img': 'pict_hit.html'
}

import views
import ssl

_flask_dir = os.getcwd().split('/ActiveAMT/')[0] + '/ActiveAMT/ActiveAMT_FLASK/'
_cert = _flask_dir + 'SSL_Creds/ssl.cert'
_key = _flask_dir + 'SSL_Creds/ssl.key'

ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
ssl_ctx.load_cert_chain(_cert, _key)
