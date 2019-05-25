#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup

url = "https://en.wikipedia.org/wiki/Lists_of_books"
html = requests.get(url).text
soup = BeautifulSoup(html, "html.parser")
filename = "list_of_books.txt"

types_of_lists = soup.find_all('ul')


def get_list_items(tag):
    """extracts an online lists items from a tag of beautifulSoup
    """
    items = tag.find_all("li")
    items_formatted = []

    for item in items:
        a = item.a
        title = a['title']
        link = a['href']

        itemf = (title, link)  # item formatted
        items_formatted.append(itemf)

    return items_formatted


index_wanted = 4

# derived from ->
# for i, li in enumerate(types_of_lists):
#     print(i)
#     get_list_items(repr(li))
#     print("\n\n\n")

list_wanted = types_of_lists[index_wanted]
items = get_list_items(list_wanted)

with open(filename, "r+") as lf:
    for title, link in items:
        link = "https://en.wikipedia.org" + link
        lf.write("title: {},\nlink: {}".format(title, link))
        lf.write("\n\n")


