# vim: set fileencoding=utf-8 noexpandtab:

# Created at the University of Maryland, Human-Computer Interaction Lab
# (c) Copyright 2011 Alexander J. Quinn
# Licensed under the MIT License (see doc/LICENSE.txt)

'''
@author: Alex Quinn
@contact: aq@cs.umd.edu
@since: January 2010
'''

from __future__ import division, with_statement


import re
_looks_like_limited_xhtml_cre = re.compile(
	r"<\s*(?:" +
	  ("|".join((
		  "a", "area", "b", "big", "blockquote", "br", "center", "cite", 
		  "code", "col", "colgroup", "dd", "del",  "dl",  "em",  "font", 
		  "h1", "h2", "h3", "h4", "h5", "h6", "hr",  "i", "img",  "ins", 
		  "li", "map", "ol", "p", "pre", "q", "small", "strong",  "sub",
		  "sup",  "table",  "tbody",  "td",   "tfoot",   "th",  "thead",
		  "tr", "u", "ul"))) +
	  r")(?:\s.*)?>",
	  re.DOTALL)

def looks_like_limited_xhtml(s):
	from crowdlib.utility.type_utils import is_string
	# See: http://docs.amazonwebservices.com/AWSMturkAPI/2008-08-02/ApiReference_FormattedContentXHTMLArticle.html
	return is_string(s) and _looks_like_limited_xhtml_cre.search(s) is not None
	
def dom_element( doc, name, *contents ):
	from crowdlib.utility.type_utils import is_string
	node = doc.createElement( name )
	for content in contents:
		if is_string(content):
			text_node = doc.createTextNode( content )
			node.appendChild( text_node )
		elif isinstance(content, int) or isinstance(content, float):
			text_node = doc.createTextNode( str(content) )
			node.appendChild( text_node )
		elif hasattr(content, "nodeType") and content.nodeType in (doc.ELEMENT_NODE, doc.TEXT_NODE, doc.CDATA_SECTION_NODE):
			node.appendChild( content )
		else:
			assert False, "Don't know how to add %s to an element: %s"%(type(content).__name__,repr( content ))
	return node

def dom_cdata( doc, content ):
	return doc.createCDATASection( content )

def _split_cdata_content(content):
	if "]]>" in content: # rare
		parts = content.split("]]>")
		num_parts = len(parts)
		new_parts = []
		i = -1
		for part in parts:
			if i > 0:
				part += "]]"
			if i + 1 < num_parts:
				part = ">"
			new_parts.append(part)
		return tuple(new_parts)
	else: # most common case
		return (content,)

def to_cdata(content):
	return "".join(("<![CDATA[" + part + "]]>") for part in _split_cdata_content(content))

def dom_cdatas(doc, content):
	return tuple(dom_cdata(doc, part) for part in _split_cdata_content(content))
	
def make_xml_document_root_element_fn_cdatas_fn(root_node_name, namespace):
	# These simplify (or at least shorten) the process of creating an XML document by building a DOM.
	import xml.dom.minidom as xdm
	import functools
	dom_impl = xdm.getDOMImplementation()
	doc = dom_impl.createDocument(namespace, root_node_name, None)
	document_element = doc.documentElement
	document_element.setAttribute( "xmlns", namespace )
	element_fn = functools.partial( dom_element, doc )
	cdatas_fn = functools.partial( dom_cdatas, doc )
	return document_element,element_fn,cdatas_fn

def text_node_content(dom_node):
	# Helper function to extract the text from a text node in an XML DOM object.
	# 
	# dom_node -- A DOM Element extracted from a DOM object created by the xml.dom.minidom module.
	from crowdlib.all_exceptions import XMLProcessingException
	childNodes = dom_node.childNodes
	if len(childNodes)==1:
		childNode = childNodes[0]
		try:
			text = childNode.wholeText
		except AttributeError:
			raise XMLProcessingException("Node %s does not have a wholeText attribute."%(dom_node.toxml()))
		text = text.strip()
		return text
	elif len(childNodes)==0:
		return ""
	else:
		raise XMLProcessingException("Expected 0 or 1 text child nodes in the DOM.  %s"%(dom_node.toxml()))

def text_in_element(node, descendent_tag_name):
	# Helper function to find a tag containing text from within a DOM or DOM Element.
	#
	# node ----------------- A DOM or DOM Element object created by the xml.dom.minidom module.
	# descendent_tag_name -- Name of the tag to search for.
	#
	# There must be exactly one element of type descendent_tag_name in the node passed in.
	from crowdlib.all_exceptions import XMLProcessingException
	child_nodes = node.getElementsByTagName(descendent_tag_name)
	if len(child_nodes)==1:
		return text_node_content(child_nodes[0])
	else:
		msg = "Expected to find only one %s tag in this %s node.  Found %d."%( 
									descendent_tag_name, node.nodeName, len(child_nodes))
		raise XMLProcessingException(msg)

def is_valid_xml(s):
	from crowdlib.utility.type_utils import is_string
	if is_string(s):
		dom = xml2dom(s, default=None)
		if dom is not None:
			dom.unlink()
			return True
	return False

def xml_in_element(node, descendent_tag_name):
	from crowdlib.all_exceptions import XMLProcessingException
	child_nodes = node.getElementsByTagName(descendent_tag_name)
	if len(child_nodes)==1:
		node = child_nodes[0]
		return node.toxml()
	else:
		msg = "Expected to find only one %s tag in this %s node.  Found %d."%( 
									descendent_tag_name, node.nodeName, len(child_nodes))
		raise XMLProcessingException(msg)

def duration_in_element(node, descendent_tag_name):
	from crowdlib.utility.type_utils import to_duration
	s = text_in_element(node, descendent_tag_name)
	return to_duration(s)

def datetime_in_element(node, descendent_tag_name):
	from crowdlib.utility.type_utils import to_date_time
	s = text_in_element(node, descendent_tag_name)
	return to_date_time(s)

def number_in_element(node, descendent_tag_name):
	s = text_in_element(node, descendent_tag_name)
	from crowdlib.utility.type_utils import to_number
	return to_number(s)

def bool_in_element(node, descendent_tag_name, value_if_true="true", value_if_false="false"):
	assert value_if_false.lower() != value_if_true.lower()
	from crowdlib.utility.type_utils import is_string
	assert is_string(value_if_false)
	assert is_string(value_if_true)
	from crowdlib.all_exceptions import XMLProcessingException
	s = text_in_element(node, descendent_tag_name)
	if s.lower()==value_if_true.lower():
		return True
	elif s.lower()==value_if_false.lower():
		return False
	else:
		raise XMLProcessingException("Found unexpected value %s.  Expected either %s or %s."%(s, value_if_true, value_if_false))

_UNDEFINED = object()
def xml2dom(xml_str, default=_UNDEFINED):
	# Parses an XML document and returns the DOM.  Uses xml.dom.minidom, but takes care of
	# an encoding	issue where xml.dom.minidom sometimes chokes on unicode data if no 
	# declaration is present.
	# 
	# See http://evanjones.ca/python-utf8.html
	import xml.dom.minidom as xdm
	import xml.parsers.expat
	try:
		try:
			dom = xdm.parseString( xml_str )
		except UnicodeError:
			dom = xdm.parseString( xml_str.encode('utf8') )
	except xml.parsers.expat.ExpatError:
		if default is not _UNDEFINED:
			return default
		else:
			raise
	return dom
