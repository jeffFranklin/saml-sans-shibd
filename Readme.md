# SAML sans shibd

This project demonstrates a SAML login to UW's IdP without Shibboleth. This
allows us to be a SAML SP without the added baggage of running shibd and
apache mod_shib. For the purpose of demonstration we use a flask application
running inside a docker container, however this could just as easily be a
django app running inside a virtualenv. The key dependency is OneLogin's 
[python3-saml package](https://github.com/onelogin/python3-saml). This demo is
also targeted at python3.6, but python2.7 would essentially be the same, albeit
with th [python-saml package](https://github.com/onelogin/python-saml).

## Three steps to SAML

There are three steps to making your app into a SAML SP (ok, four if you include
the SP registration, which this demo already has done but your SP will certainly
need to do).

### Add your SP config

python-saml has a can be a json file or a python dict. We go the dict route for
this demo, which you can see [here](saml.py). The idp section likely stays the
same, your `entityId` and `assertionConsumerService.url` are possibly all you
need to change.

### Add a login redirect

For our flask app you can find it as `@app.route('/login')` in [app.py](app.py).
It initiates a saml request to redirect to the IdP.

### Add a SAML response handler

We do this here as `@app.route('/Shibboleth.sso/SAML2/POST', methods=['POST'])`
in [app.py](app.py). We're piggybacking off of an existing shib SP, hence
the `/Shibboleth.sso/SAML2/POST`, but you will probably want to register a
better-named endpoint that the IdP will post back to.

## Run instructions

Only assumption is that you have docker installed. The openssl command generates
a cert/key pair on the fly, however any cert/key will do. Changing your hosts
setting depends on your platform, of course.

```
echo '127.0.0.1   docker.internal' >> /etc/hosts
# cd into saml-sans-shibd. `pwd` could be replaced with the full directory
# of your project.
openssl req -x509 -newkey rsa:4096 -nodes \
	-out cert.pem -keyout key.pem -days 365

docker run --name flaskapp --restart=always -p 443:443 -v `pwd`:/app \
       -d jazzdd/alpine-flask:python3 -d
```

The last `-d` runs flask in debug mode, without nginx/uwsgi. This allows us to
change our app on the fly, with the local changes being picked up and flask
being restarted. This also run https directly from flask. The task of getting
https working against nginx is an exercise left to the user.

The initial `docker run` takes a couple minutes to install and build packages.
You can tail the logs via `docker logs -f flaskapp` to see when it's ready.
`docker stop flaskapp` when you're done.


Now point your browser at `https://docker.internal`, authenticate, and 
see your attributes.

## Results

Initial page:

![page 1](images/page1.png)

IdP page:

![page 2](images/page2.png)

Page displaying attributes after a succesful authentication:

![page 3](images/page3.png)
