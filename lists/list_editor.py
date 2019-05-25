#!/usr/bin/env python3
from bs4 import BeautifulSoup, NavigableString

import urllib
import requests
import json

HOME_LINK = "https://en.wikipedia.org"
FILE_NAME = "list_of_books.json"

with open(FILE_NAME) as f:
    books = json.load(f)
    book_cs = list(books.keys())  # book categories


def get_first_wikipedia_para(title):
    """get the first paragraph from a wikipedia page"""
    link = "https://en.wikipedia.org/w/api.php?format=json&action=query&prop=extracts&exintro&explaintext&redirects=1&titles={}" 
    link = link.format(title)
    print(title)
    data = requests.get(link).json()
    print(link)
    pages = data['query']['pages']
    page_names = list(pages.keys())
    para = pages[page_names[0]]['extract']
    return para

def extract_lists(link, print_index=0):
    """extract all lists from a url"""
    print(link)
    html = requests.get(link).text
    soup = BeautifulSoup(html, "html.parser")
    lists = soup.find_all("ul")
    nicer_list = []

    for li in lists:
        list_items = li.find_all("li")
        this_list = []
        for num, item in enumerate(list_items):
            # representable item, these look better when
            # printed on screen
            item = item.find("a")
            if item is not None:
                reper_item = [item.get("title", ""), item.get("href", "")]

                if num == print_index:
                    print(reper_item)

                if "(page does not exist)" not in reper_item[0]:
                    reper_item[1] = HOME_LINK + reper_item[1]
                    this_list.append(reper_item)

        nicer_list.append(this_list)

    return nicer_list


def get_contents(contents):
    desc_with_contents = []
    for title, link in contents:
        if title != '':
            quoted_title = urllib.parse.quote(title)
            paragraph = get_first_wikipedia_para(quoted_title)
            book = {
                    'title': title,
                    'description': paragraph
                   }

            print(title)
            print(paragraph)
            print("-------------------")
            desc_with_contents.append(book)

    return desc_with_contents

def print_links(url):
    html = requests.get(url).text
    soup = BeautifulSoup(html)
    links = soup.find_all("a")
    for i, link in enumerate(links):
        link_loc = link.get('href', None)
        link_title = link.get('title', None)
        if link_loc and link_title:
            print(i, link_title)

# each category will require a different method to
# extract it,
# since all html pages are formatted differently

# link 4
category = book_cs[4]
category_link = books[category]["link"]
# print_links(category_link)

links = [
"https://en.wikipedia.org/wiki/The_Secret_Life_of_Salvador_Dal%C3%AD",
"https://en.wikipedia.org/wiki/Period_Piece_(book)",
"https://en.wikipedia.org/wiki/Moe_Howard_and_the_Three_Stooges",
"https://en.wikipedia.org/wiki/Pryor_Convictions",
"https://en.wikipedia.org/wiki/Moab_Is_My_Washpot",
"https://en.wikipedia.org/wiki/Born_Standing_Up",
"https://en.wikipedia.org/wiki/My_Shit_Life_So_Far",
"https://en.wikipedia.org/wiki/American_on_Purpose",
"https://en.wikipedia.org/wiki/Memoirs_of_a_Professional_Cad",
"https://en.wikipedia.org/wiki/Me_and_the_Orgone",
"https://en.wikipedia.org/wiki/The_Moon%27s_a_Balloon",
"https://en.wikipedia.org/wiki/Dear_Me_(book)",
"https://en.wikipedia.org/wiki/Jakhan_Choto_Chilam",
"https://en.wikipedia.org/wiki/Something_Like_an_Autobiography",
"https://en.wikipedia.org/wiki/Confessions_of_an_Actor",
"https://en.wikipedia.org/wiki/On_Acting",
"https://en.wikipedia.org/wiki/Growing_Up_Brady",
"https://en.wikipedia.org/wiki/I_Am_Spock",
"https://en.wikipedia.org/wiki/Leaving_a_Doll%27s_House",
"https://en.wikipedia.org/wiki/Still_Me",
"https://en.wikipedia.org/wiki/I_Am_Jackie_Chan",
"https://en.wikipedia.org/wiki/The_Measure_of_a_Man:_A_Spiritual_Autobiography"
]
page_names = []
init_thing = "https://en.wikipedia.org/wiki/"

for link in links:
    link = link[len(init_thing):]
    page_names.append(link)

books_n_details = []
for name in page_names:
    para = get_first_wikipedia_para(name)
    title = urllib.parse.unquote(name)
    book = dict(title=title, description=para)
    books_n_details.append(book)

print(books_n_details)
print(books[category])
books[category]["books"] = books_n_details

UPDATED_FILE_NAME = 'updated_' + FILE_NAME

if True:
    with open(UPDATED_FILE_NAME, 'w') as jsonf:
        json.dump(books, jsonf)
