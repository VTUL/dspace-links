activate_this = '/var/www/dspace-links/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

from dspace_links import app as application
