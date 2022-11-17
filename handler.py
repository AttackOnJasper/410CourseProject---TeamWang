from http.server import BaseHTTPRequestHandler, HTTPServer
import json

import urllib.request, urllib.parse, urllib.error
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

HOST_NAME = 'localhost'
PORT = 8080



# def calculateDocLM(inputList) {
# 	aggregatedInput = ' '.join(inputList)
# 	inputWithoutSpecialChar = re.sub('[^A-Za-z\space]','', aggregatedInput)
# 	tokens = inputWithoutSpecialChar.split(' ')
# 	wordDist = Counter(tokens)
# }

class Processor:
	def __init__(self):
		self.model = pipeline('fill-mask', model='bert-base-uncased')

	def process(self, urls):
		sentences = self.read_urls(urls)
		for sentence in sentences:
			# Tokenization
			words = word_tokenize(sentence)

			# POS tagging for lexical analysis
			pos_tagged_text = nltk.pos_tag(words)

			# Masking every single noun of the sentence at a time for keyword probability analysis
			for text, tag in pos_tagged_text:
				if 'NN' in tag: # check if tag is NN, NNS, or NNP (i.e. noun)
					input = sentence.replace(text, '[MASK]')
					output = self.model(input)
					print(output)

	def read_urls(self, urls):
		inputList = []
		# TODO: see if there are ways to batch read urls
		for url in urls:
			req = Request(url)
			try:
				response = urlopen(req)
			except HTTPError as e:
				print('The server couldn\'t fulfill the request.')
				print('Error code: ', e.code)
			except URLError as e:
				print('We failed to reach a server.')
				print('Reason: ', e.reason)
			else:
				html = response.read()
				soup = BeautifulSoup(html, 'html.parser')
				contents = soup('title') + soup('p')
				inputList = inputList + [data.getText() for data in contents]
		aggregatedInput = ' '.join(inputList)
		sentences = aggregatedInput.split('\\.')
		return sentences

class RecommendationRequestHandler(BaseHTTPRequestHandler):

	def __init__(self, request, client_address, server):
		print("Initializing RecommendationRequestHandler.")
		self.processor = Processor()
		super().__init__(request, client_address, server)
		

	def _set_headers(self):
		self.send_response(200)
		self.send_header('Content-Type', 'text/html')
		self.end_headers()

	def do_POST(self):
		self._set_headers()
		content_len = int(self.headers.get('Content-Length'))
		post_body = self.rfile.read(content_len)
		print(post_body)
		json_data = json.loads(post_body)
		if 'urls' not in json_data:
			self.wfile.write(bytes("Urls are not presented in the POST body.", "utf-8"))
		print(json_data['urls'])
		self.processor.process(json_data['urls'])


	def do_GET(self):
		self._set_headers()
		self.wfile.write(bytes("<html><head><title>CS410 Project - Team Wang</title></head>", "utf-8"))
		self.wfile.write(bytes("<p>Request path: %s</p>" % self.path, "utf-8"))
		self.wfile.write(bytes("<body>", "utf-8"))
		self.wfile.write(bytes("<p>GET operation is just a test. Please use POST </p>", "utf-8"))
		self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__": 
	webServer = HTTPServer((HOST_NAME, PORT), RecommendationRequestHandler)
	print("Server started http://%s:%s" % (HOST_NAME, PORT))

	try:
		webServer.serve_forever()
	except KeyboardInterrupt:
		pass
	webServer.server_close()
	print("Server stopped.")