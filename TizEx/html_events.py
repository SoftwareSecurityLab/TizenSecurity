from bs4 import BeautifulSoup
from shared import *

events = ['onclick', 'onmouseover']

def event(element):
    # element is a BeautifulSoup object. this function is a generator which returns all the event attributes
    # of an element. 
    # for example returns 'onclick', 'onmouseover' for element <div onclick=alert(1) onmouseover=alert(2)></div>
    try:
        for attr in element.attrs:
            if attr in events:
                yield attr
    except AttributeError:
        return None


def extract_call_backs_element(element_soup):
    # gets an element of BeautifulSoup obj. extracts all its event callbacks. and returns them
    # e.g: element='<div onclick=alert(1) onmouseover=alert(2)></div>' returns a string
    # -> alert(1);alert(2);

    res = ''
    for item in event(element_soup):
        res += element_soup[item] + ';'
    return res

def write_to_file(file_handler, string):
    # wrties string to file.
    if len(string):
        print(string, file=file_handler)  


def extract_call_backs_html(path_to_html):
    # gets path to an html file. extracts all the callback functions in html such as
    # onclick, onmouseover
    # then saves these callbacks in a file. which will be appended to the main file in the end
    
    events_file = open(event_file_path, 'w')

    soup = BeautifulSoup(open(path_to_html), 'html.parser')
    element = soup.find()  # first element of html

    while element:
        res = extract_call_backs_element(element)
        write_to_file(events_file, res)
        element = element.next_element

    events_file.close()

    

