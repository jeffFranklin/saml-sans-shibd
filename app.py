import os
from flask import request, session
import flask
from urllib.parse import urlparse
from onelogin.saml2.auth import OneLogin_Saml2_Auth
import saml  # TODO: make relative import

app = flask.Flask(__name__, template_folder='.')
app.config['SECRET_KEY'] = 'change this secret or else'


class FlaskSaml(OneLogin_Saml2_Auth):
    def __init__(self, request):
        """Init a OneLogin authentication object from a flask request."""
        request_data = {
            'https': 'on' if request.scheme == 'https' else 'off',
            'http_host': request.host,
            'server_port': urlparse(request.url).port,
            'script_name': request.path,
            'get_data': request.args.copy(),
            'post_data': request.form.copy()
        }
        super().__init__(request_data, old_settings=saml.CONFIG)

    def get_attributes(self):
        """
        Return a dict of SAML attributes, mapping then names to friendlier
        ones we could use internally.
        """
        attribute_map = {
            'urn:oid:0.9.2342.19200300.100.1.1': 'uwnetid',
            'urn:oid:1.3.6.1.4.1.5923.1.1.1.1': 'affiliations',
            'urn:oid:1.3.6.1.4.1.5923.1.1.1.6': 'eppn',
            'urn:oid:1.3.6.1.4.1.5923.1.1.1.9': 'scopedAffiliations'
        }
        return {attribute_map.get(key, key): value
                for key, value in super().get_attributes().items()}


@app.route('/')
def index():
    attributes = list(session.get('samlAttributes', {}).items())
    return flask.render_template('index.html', attributes=attributes)


@app.route('/login')
def login():
    auth = FlaskSaml(request)
    return flask.redirect(auth.login(return_to=request.host_url))


@app.route('/logout')
def logout():
    session.clear()
    return flask.redirect('/')


@app.route('/Shibboleth.sso/SAML2/POST', methods=['POST'])
def sso():
    auth = FlaskSaml(request)
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        raise Exception(errors)
    session['samlAttributes'] = auth.get_attributes()
    return flask.redirect(auth.redirect_to(request.form['RelayState']))


if __name__ == "__main__":
    sslctx = ('cert.pem', 'key.pem')
    app.run(host='0.0.0.0', ssl_context=sslctx, port=443, debug=True)

