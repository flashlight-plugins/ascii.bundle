import logging
logger = logging.getLogger()
logger.setLevel(logging.NOTSET)
handler = logging.FileHandler("/Users/cosmo/work/temp/flashlight/ascii.log")
handler.setLevel(logging.NOTSET)
handler.setFormatter(logging.Formatter('%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'))
logger.addHandler(handler)

def appearance():
	import Foundation
	dark_mode = Foundation.NSUserDefaults.standardUserDefaults().persistentDomainForName_(Foundation.NSGlobalDomain).objectForKey_("AppleInterfaceStyle") == "Dark"
	return "dark" if dark_mode else "light"

class Entry:
	def __init__(self, line, idx=-1, score=1.0):
		self.line = line
		self.score = score
		self.idx = idx

def build_ascii_dict():
	# prepare ascii dictionary
	import os
	with open(os.path.join(os.path.dirname(__file__), "ascii.txt"), "r") as f:
		asciilist = f.readlines()
	asciiindices = {}
	asciilist = [line.strip() for line in asciilist]
	asciilist = list(filter(lambda line: len(line) > 0, asciilist))
	for i in range(len(asciilist)):
		line = asciilist[i]
		wholewords = [word.strip() for word in line.split(",")]
		if len(wholewords) == 3:
			line = "%s (%s): %s" % tuple(wholewords)
		elif len(wholewords) == 2:
			line = "%s (%s)" % tuple(wholewords)
		for wholeword in wholewords:
			wholeword = wholeword.lower()
			if wholeword not in asciiindices:
				asciiindices[wholeword] = []
			asciiindices[wholeword].append(Entry(line, idx = i, score = 1.0))
			words = list(filter(lambda word: len(word) > 1, [word.strip() for word in wholeword.split(" ")]))
			if len(words) == 1:
				continue
			for word in words:
				word = word.lower()
				if word not in asciiindices:
					asciiindices[word] = []
				asciiindices[word].append(Entry(line, idx = i, score = 1.0 / len(words)))
		asciilist[i] = line
	return asciilist, asciiindices

def format_string(text, **kwargs):
	for k in kwargs:
		text = text.replace('{' + k + '}', "{}".format(kwargs[k]))
	return text

def build_html(entries):
	# prepare html
	import os
	with open(os.path.join(os.path.dirname(__file__), "result.html"), "r") as f:
		html = f.read()
	html = format_string(html, appearance=appearance())
	rowtmpl_start_tag = '{%template:begin%}'
	rowtmpl_end_tag = '{%template:end%}'
	rowtmpl_start = html.find(rowtmpl_start_tag)
	rowtmpl_end = html.find(rowtmpl_end_tag)
	if rowtmpl_start < 0 or rowtmpl_end < 0:
		return_html = ""
	else:
		rowtmpl_html = html[rowtmpl_start+len(rowtmpl_start_tag):rowtmpl_end]
		listhtml = ""
		for x in sorted(entries, key=lambda x: -x.score):
			code = x.idx
			desc = x.line
			listhtml += format_string(rowtmpl_html,
				hex = "0x%02x" % code,
				oct = code,
				desc = desc
			)
		return_html = html[:rowtmpl_start] + listhtml + html[rowtmpl_end+len(rowtmpl_end_tag):]
	return return_html
	

def results(fields, original_query):
	# logger.info("fields = {}".format(fields))
	try:
		if "~desc" in fields:
			asciilist, asciiindices = build_ascii_dict()
			query = fields["~desc"].strip().lower()
			words = list(filter(lambda word: len(word) > 0, [word.strip() for word in query.split(" ")]))
			scores = [0 for i in range(len(asciilist))]
			for word in words:
				if word in asciiindices:
					entries = asciiindices[word]
					for entry in entries:
						scores[entry.idx] += entry.score
			entries = [Entry(asciilist[i], idx=i, score=scores[i]) for i in range(len(scores))]
			entries = list(filter(lambda x: x.score > 0, entries))
			return_html = build_html(entries)
			# logger.debug(return_html)
			return {
				"title": "Search for ASCII code of '{0}'".format(query),
				"html": return_html,
				'webview_transparent_background': True
			}
		elif "~code" in fields:
			query = fields["~code"]
			asciilist, asciiindices = build_ascii_dict()
			try:
				if query[:2].lower() == "0x":
					code = int(query[2:], base=16)
				else:
					code = int(query)
			except ValueError:
				code = -1
			if code >= 0 and code < len(asciilist):
				entries = [Entry(asciilist[code], idx=code)]
			else:
				entries = []
			return {
				"title": "View ASCII code {0}".format(query),
				"html": build_html(entries),
				'webview_transparent_background': True
			}
		else:
			return {}
	except Exception as e:
		import traceback
		logger.error(traceback.format_exc(e))
