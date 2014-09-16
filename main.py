#!/usr/bin/python
#
# Copyright 2011 Google Inc. All Rights Reserved.

"""A simple guest book app that demonstrates the App Engine search API."""


from cgi import parse_qs
from datetime import datetime
import os
import string
import urllib
from urlparse import urlparse

import webapp2
from webapp2_extras import jinja2

from google.appengine.api import search
from google.appengine.api import users        

import logging

_INDEX_NAME = 'greeting'

# _ENCODE_TRANS_TABLE = string.maketrans('-: .@', '_____')


logging.warning('hello1') 
init = 0

class BaseHandler(webapp2.RequestHandler):
    """The other handlers inherit from this class.  Provides some helper methods
    for rendering a template."""

    @webapp2.cached_property
    def jinja2(self):
      return jinja2.get_jinja2(app=self.app)

    def render_template(self, filename, template_args):
      self.response.write(self.jinja2.render_template(filename, **template_args))


class MainPage(BaseHandler):
    """Handles search requests for comments."""
    init1 = 0
    def get(self):
        """Handles a get request with a query."""  
        logging.warning('MainPage-get')
        uri = urlparse(self.request.uri)
        query = ''
        if uri.query:
            query = parse_qs(uri.query)
            query = query['query'][0]

        # sort results by author descending
        expr_list1 = [search.SortExpression(
            expression='author', default_value='',
            direction=search.SortExpression.DESCENDING)]
        expr_list = [search.SortExpression(
            expression='_rank', default_value='',
            direction=search.SortExpression.DESCENDING)]
        # construct the sort options
        sort_opts = search.SortOptions(
             expressions=expr_list)
        query_options = search.QueryOptions(
            limit=10,
#            snippeted_fields=['comment'],
#            returned_expressions=[search.FieldExpression(name='rank2', expression='_order_id * 2')],
            sort_options=sort_opts)
        query_obj = search.Query(query_string=query, options=query_options)
        results = search.Index(name=_INDEX_NAME).search(query=query_obj)
        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'results': results,
            'number_returned': len(results.results),
            'url': url,
            'url_linktext': url_linktext,
            'query':query,
        }
        self.render_template('index.html', template_values)


def CreateDocument(author, fields, rank):
    """Creates a search.Document from content written by the author."""
    if author:
        nickname = author.nickname().split('@')[0]
    else:
        nickname = 'anonymous'   
    fields.append(search.TextField(name='author', value=nickname))
#	FIXME: try full dates too!
#    fields.append(search.DateField(name='date', value=datetime.now().date()))
    fields.append(search.DateField(name='date', value=datetime.now()))

    gp =    search.GeoPoint(50.,50.)   
#    fields.append(search.GeoField(name='geo1', value=gp))
#    fields.append(search.GeoField(name='geo2', value=search.GeoPoint(40.,40.)))
    # Let the search service supply the document id. 
    logging.warning(fields) 
    if rank:
        doc =  search.Document(fields=fields, rank=rank)
    else:
        doc =  search.Document(fields=fields)
    return doc

def FlushIndex():
    doc_index = search.Index(name=_INDEX_NAME)

    while True:
        # Get a list of documents populating only the doc_id field and extract the ids.
        document_ids = [document.doc_id
                        for document in doc_index.get_range(ids_only=True)]
        if not document_ids:
            break
        # Delete the documents for the given ids from the Index.
        doc_index.delete(document_ids)



class Flush(BaseHandler):
    """Handles requests to flush index."""

    def post(self):
        FlushIndex()
        self.redirect('/')


class Comment(BaseHandler):
    """Handles requests to index comments."""

    def post(self):
        """Handles a post request."""
        author = None
        if users.get_current_user():
            author = users.get_current_user()

        if self.request.get('button')=='Flush Index': 
            logging.warning('WE FLUSH')

        if self.request.get('button')=='Add Document': 
            logging.warning('WE ADD')   
            fields = []     
            content = self.request.get('content')
            logging.warning('test for content') 
            if content:  
                logging.warning('test for content1')
                fields = [search.TextField(name='comment', value=content)] 
            html = self.request.get('html')
            logging.warning('test for html') 
            if html: 
                fields = [search.HtmlField(name='html', value=html)]
            number = self.request.get('number')  
            logging.warning('test for number')
            if number:
                fields.append(search.NumberField(name='number', value=float(number)))
            atom = self.request.get('atom') 
            logging.warning('test for atom')
            if atom:
                fields.append(search.AtomField(name='atom', value=atom))
            rank = self.request.get('rank')  
            logging.warning('test for rank')
            if rank:
                rank = int(rank)
            latti = self.request.get('lat')
            longi = self.request.get('long')  
            logging.warning('test for geo')
            logging.warning(latti)
            logging.warning(longi)
            if (latti!="" and longi!=""):  
                logging.warning('geoppppppp')
                fields.append(search.GeoField(name='geo', value=search.GeoPoint(float(latti),float(longi))))
            if len(fields) > 0:
                search.Index(name=_INDEX_NAME).put(CreateDocument(author, fields, rank))
            else: 
                logging.warning('empty form')
            self.redirect('/')

        if self.request.get('button')=='Search': 
            logging.warning('WE SEARCH')
            query = self.request.get('search')  
            self.redirect('/?' + urllib.urlencode(
                #{'query': query}))
                {'query': query.encode('utf-8')}))  

class Comment2(BaseHandler):
    """Handles requests to index comments."""

    def post(self):
        """Handles a post request."""
        author = None
        if users.get_current_user():
            author = users.get_current_user()

        content = self.request.get('content')
        query = self.request.get('search')  
        if query:  
            if query == 'flush':  
               logging.warning('flush')  
               FlushIndex()
            self.redirect('/?' + urllib.urlencode(
                #{'query': query}))
                {'query': query.encode('utf-8')}))  
        else:
	        fields = []
	        if content: 
		        fields = [search.TextField(name='comment', value=content)]
	        html = self.request.get('html') 
	        if html: 
		        fields = [search.HtmlField(name='html', value=html)]
	        number = self.request.get('number')
	        if number:
	            fields.append(search.NumberField(name='number', value=float(number)))
	        atom = self.request.get('atom') 
	        if atom:
	            fields.append(search.AtomField(name='atom', value=atom))
	        latti = self.request.get('lat')
	        longi = self.request.get('long') 
	        if (latti!="" and longi!=""):  
		        logging.warning('geoppppppp')
		        fields.append(search.GeoField(name='geo', value=search.GeoPoint(float(latti),float(longi))))
	        if len(fields) > 0:
	            search.Index(name=_INDEX_NAME).put(CreateDocument(author, fields))
	        else: 
	            logging.warning('empty form')
	        self.redirect('/')


application = webapp2.WSGIApplication(
    [('/', MainPage),
     ('/sign', Comment),
     ('/flush',Flush)],
    debug=True)
