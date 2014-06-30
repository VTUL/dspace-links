"""Provides the MetaArchive LOCKSS crawler links to the objects in a collection."""

from bs4 import BeautifulSoup
from collections import namedtuple
from flask import Flask, render_template
from lxml import etree
import requests

app = Flask(__name__)

# REQ is the URL used to query for collections.
REQ = 'http://vtechworks.lib.vt.edu/oai/request?verb=ListRecords'
# PAGE is a blank page for BeautifulSoup to add the results to.
PAGE = '<html><head><title>%s</title></head><body><h1>%s</h1><p><ul></ul></p></body></html>'

# Using a named tuple because list indices are fickle and not maintainence friendly.
IdentifierParts = namedtuple('IdentifierParts', ['protocol', 'host', 'identifier'])

class DSpaceCollection:
    def __init__(self, collection):
        """Create a new DSpace Collection, and find all the identifiers in the set."""

        self._collection = collection
        self._identifiers = []

        token = self.add_identifiers()

        while token is not None and len(self._identifiers) < int(token.get('completeListSize')):
            token = self.add_identifiers(token.text)

    def add_identifiers(self, token=None):
        """Add identifiers to the collection, and return a resumption token, if applicable."""

        if token is None:
            dim_file = requests.get(REQ + '&metadataPrefix=dim&set=' + self._collection)
        else:
            dim_file = requests.get(REQ + '&resumptionToken=' + token)

        xml = etree.XML(bytes(dim_file.text, 'utf-8'))
        new_identifiers = [id.text for id in xml.findall('{*}ListRecords/{*}record/{*}header/{*}identifier')]
        self._identifiers.extend(new_identifiers)

        return xml.find('{*}ListRecords/{*}resumptionToken')

    def link_generator(self):
        """Generate urls for the full record of an object in the collection."""

        for identifier in self._identifiers:
            # On 05/05/2014, the identifier text looks like this: "oai:vtechworks.lib.vt.edu:10919/19700"
            # Unpack list from .split() with *arg and create a named tuple.
            id_parts = IdentifierParts(*identifier.split(':'))
            yield 'http://' + id_parts.host + '/handle/' + id_parts.identifier + '?show=full'

    def has_records(self):
        """Whether or not the collection has any records."""

        return len(self._identifiers) > 0

@app.route('/manifest/<collection>')
def manifest(collection):
    """Send the static manifest page"""

    collection = collection.strip(' \t\r\n\'";:&=<>(){}[]')
    return render_template('manifest.html', collection=collection)

@app.route('/<collection>')
def linkify_dim_collection(collection):
    """Retrieve a collection and make links for all its objects, or provide an error."""

    collection = collection.strip(' \t\r\n\'";:&=<>(){}[]')
    col = DSpaceCollection(collection)
    output = BeautifulSoup(PAGE % (collection, 'Links for ' + collection))
    if col.has_records():
        status_code = 200
        ul = output.find('ul')
        for link in col.link_generator():
            anchor = output.new_tag('a', href=link)
            anchor.string = link
            li = output.new_tag('li')
            li.append(anchor)
            ul.append(li)
    else:
        status_code = 404
        output.html.head.title.string = 'No Matching Records'
        output.html.body.h1.string = 'Error!'
        output.html.body.p.string = 'The requested collection, "%s", contained no matching records.' % collection
        # As best we know, this means the collection doesn't exist.
    return output.prettify(), status_code

if __name__ == '__main__':
    #app.debug = True
    app.run()
