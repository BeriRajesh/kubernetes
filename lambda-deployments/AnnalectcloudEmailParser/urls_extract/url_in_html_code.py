from bs4 import BeautifulSoup

def url_in_html_code(html_code):
	"""
	Extracts URLs from html string.
	"""
	urls = []
	soup = BeautifulSoup(html_code, "html.parser")
	for link in soup.find_all(attrs={'class': 'article-additional-info'}):
		for link in item.find_all('a'):
			#if url and "https" in url or "http" in url:		# is it safe?
			urls.append(link.get("href"))
	return urls