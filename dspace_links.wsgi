# Via http://flask.pocoo.org/docs/deploying/mod_wsgi/
# TODO: Correct path.
activate_this = '/path/to/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from dspace_links import app as application
