import requests
from bs4 import BeautifulSoup

response = requests.get("https://fmovies.media")

soup = BeautifulSoup(response.text, "html.parser")
print(soup.prettify())
