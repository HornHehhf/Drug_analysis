from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):

    def handle_data(self, data):
        print(data)