import re

def get_urls_from_plain_part(email_data):
	"""
	Extracts URLs from plain text string.
	"""
	try:
		pattern = "abcdefghijklmnopqrstuvwxyz0123456789./\~#%&()_-+=;?:[]!$*,@'^`<{|\""
		indices = [m.start() for m in re.finditer('http://', email_data)]
		indices.extend([n.start() for n in re.finditer('https://', email_data)])
		
		urls = []
		if indices:
			if len(indices) > 0:
				new_lst = zip(indices, indices[1:])
				for x, y in new_lst:
					tmp = email_data[x:y]
					url = ""
					for ch in tmp:
						if ch.lower() in pattern:
							url += ch
						else:
							break
					urls.append(url)
			tmp = email_data[indices[-1]:]
			url = ""
			for ch in tmp:
				if ch.lower() in pattern:
					url += ch
				else:
					break
			urls.append(url)
			return urls
		return []
	except Exception as err:
		print("ERROR - Exception when parsing plain text for urls: %s" % err)
		return []