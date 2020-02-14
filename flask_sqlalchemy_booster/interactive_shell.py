from contextlib import contextmanager

import json
from pprint import PrettyPrinter
from toolspy import merge


def run_interactive_shell(app, db):

    app.config['WTF_CSRF_ENABLED'] = False

    # Needed for making the console work in app request context
    ctx = app.test_request_context()
    ctx.push()
    # app.preprocess_request()

    # The test client. You can do .get and .post on all endpoints
    client = app.test_client()

    get = client.get
    post = client.post
    put = client.put
    patch = client.patch
    delete = client.delete


    # Helper method for sending JSON POST.

    def load_json(resp):
        return json.loads(resp.data)

    def jpost(url, data, raw=False):
        response = client.post(
            url, data=json.dumps(data),
            content_type="application/json")
        if raw:
            return response
        return load_json(response)

    def jput(url, data, raw=False):
        response = client.put(
            url, data=json.dumps(data),
            content_type="application/json")
        if raw:
            return response
        return load_json(response)

    def jpatch(url, data, raw=False):
        response = client.patch(
            url, data=json.dumps(data),
            content_type="application/json")
        if raw:
            return response
        return load_json(response)

    def jget(url, **kwargs):
        return load_json(get(url, **kwargs))


    # Use this in your code as `with login() as c:` and you can use
    # all the methods defined on `app.test_client`
    @contextmanager
    def login(email=None, password=None):
        client.post('/login', data={'email': email, 'password': password})
        yield
        client.get('/logout', follow_redirects=True)

    q = db.session.query
    add = db.session.add
    addall = db.session.add_all
    commit = db.session.commit
    delete = db.session.delete

    sitemap = app.url_map._rules_by_endpoint

    routes = {}
    endpoints = {}

    pprint = PrettyPrinter(indent=4).pprint

    for rule in app.url_map._rules:
        routes[rule.rule] = rule.endpoint
        endpoints[rule.endpoint] = rule.rule
    try:
        import IPython
        IPython.embed()
    except:
        import code
        code.interact(local=merge(locals(), globals()))


