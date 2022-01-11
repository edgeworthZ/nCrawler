import requests
from requests.exceptions import HTTPError
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen
import os, codecs
import os.path
import re

headers = {
    'User-Agent': 'nCrawler',
    'From': 'nutawut.n@ku.th'
}
target_urls = ['https://registrar.ku.ac.th',
               'https://sis.ku.ac.th',
               'https://www.ku.ac.th',
               'http://www.cai.ku.ac.th',
               'http://www.coop.ku.ac.th',
               'http://dna.kps.ku.ac.th',
               'https://www.ee.ku.ac.th',
               'https://std.regis.ku.ac.th',
               'https://knowbita.cpe.ku.ac.th',
               'https://lms.ku.ac.th',
               'http://www.grad.ku.ac.th',
               'http://ifrpd.ku.ac.th',
               'http://www.vettech.ku.ac.th',
               'http://www.ee.ku.ac.th',
               'http://www.eto.ku.ac.th',
               'http://www.interprogram.ku.ac.th',
               'https://eassess.ku.ac.th',
               'https://www.cpe.ku.ac.th',
               'http://www.east.human.ku.ac.th',
               'http://ase.eng.ku.ac.th',
               'http://www.gerd.eng.ku.ac.th',
               'http://www.kps.ku.ac.th',
               'http://dnatec.kps.ku.ac.th',
               'http://www.kus.ku.ac.th',
               'http://www.bce.eco.ku.ac.th',
               'http://doipui.aerdi.ku.ac.th',
               'http://www.mfpe.eng.ku.ac.th',
               'http://www.wre.eng.ku.ac.th',
               'http://vet.ku.ac.th',
               'http://iup.eng.ku.ac.th',
               'http://doed.edu.ku.ac.th']

frontier_q = ['']
visited_q = []
WebToCrawl = 10000
count = 0
index = 0
robots = []
sitemap = []

def get_page(url):
    global headers
    text = ''
    try:
        response = requests.get(url, headers=headers, timeout=2)
        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Python 3.6
    except Exception as err:
        print(f'Other error occurred: {err}')  # Python 3.6
    else:
        #print('Success!')
        # Filter only html
        if 'text/html' in response.headers['content-type']:
            text = response.text
        else:
            text = ''
    #return text.lower()
    return text

def link_parser(raw_html):
    urls = [];
    pattern_start = '<a href="';  pattern_end = '"'
    index = 0;  length = len(raw_html)
    while index < length:
        start = raw_html.find(pattern_start, index)
        if start > 0:
            start = start + len(pattern_start)
            end = raw_html.find(pattern_end, start)
            link = raw_html[start:end]
            if len(link) > 0:
                if link not in urls:
                    urls.append(link)
            index = end
        else:
            break
    return urls

# param 'links' is a list of extracted links to be stored in the queue
def enqueue(links):
    global frontier_q
    for link in links:
        if link not in frontier_q and link not in visited_q:
            #print('append:',link)
            frontier_q.append(link)

# FIFO queue
def dequeue():
    global frontier_q
    current_url = frontier_q[0]
    frontier_q = frontier_q[1:]
    return current_url

def check_robots(url_base):
    try:
        checker = urlopen(url_base + '/robots.txt')
        string = checker.read().decode('utf8')

        print(url_base + '/robots.txt')

        found = False
        has_sitemap = False
        for line in string.splitlines():
            if line == 'User-agent: *':
                found = True
            if 'Sitemap:' in line:
                has_sitemap = True
        if found:
            robots.append(url_base.replace('https://','').replace('http://',''))
            print('found robots.txt')
        if has_sitemap:
            sitemap.append(url_base.replace('https://','').replace('http://',''))
            print('found sitemap')
    except:
        check = 'none'


def start_crawl(seed_url):
    global count, WebToCrawl, frontier_q, visited_q, target_urls
    check_robots(seed_url)

    frontier_q = ['']
    visited_q = []
    
    while count < WebToCrawl:

        # Check for available links
        if len(frontier_q) < 1:
            print('Going to next site...')
            break

        try:
            sub_url = dequeue()
            current_url = seed_url+sub_url
            print('Start crawling(',count+1,'):',current_url)
            visited_q.append(sub_url)
            
            raw_html = get_page(current_url)

            # This isn't a html page
            if len(raw_html) < 1:
                print('Skip this page')
                continue

            count = count + 1
            
            #if current_url == 'https://www.ku.ac.th/tuition-fees/':
            #    print(raw_html)
            extracted_links = link_parser(raw_html)
            #print('Links:',extracted_links)
            # Filter Links
            filtered_links = []
            for link in extracted_links:

                # remove ../
                link = link.replace('../','')

                # Check url looping
                if '&summary=' in link:
                    head, sep, tail = link.partition('&summary=')
                    # ignore sep & tail
                    link = head

                p = urlparse(link)
                # ignore files
                ext = os.path.splitext(link)[1]
                if len(ext) > 0:
                    if ext != '.html' and ext != '.htm' and ext != '.php':
                        continue
                
                if seed_url in link:
                    pp = link.split(seed_url)[1]
                    #print('pp',pp)
                    filtered_links.append(pp)
                elif 'http' in link:
                    if 'ku.ac.th' in link:
                        host_name = p.scheme + '://' + p.netloc
                        #print('pending host_name:',host_name)
                        if not host_name in target_urls:
                            target_urls.append(host_name)
                else:
                    if link[0] != '/':
                        #print('Lastest: /'+link)
                        filtered_links.append('/'+link)
                    else:
                        #print('Lastest2: '+link)
                        filtered_links.append(link)
                    
            #print('filtered_links:',filtered_links)
            enqueue(filtered_links)
            #print('Sub Directory:',frontier_q)

            # Create (sub)directories with the 0o755 permission
            # param 'exist_ok' is True for no exception if the target directory already exists

            # os mkdir limit
            current_url = (current_url[:63]) if len(current_url) > 63 else current_url

            o = urlparse(current_url)
            formatted_path = re.sub(r'[^-_.#=\nA-Za-z0-9/]+', '', current_url.split(seed_url)[1])
            path = 'html/'+o.hostname+formatted_path
            #print(path)
            # Write content into a file
            #raw_html = '<html><body><a href="http://test1.com">test1</a><br><a href="http://test2.com">test2</a></body></html>'
            abs_file = path
            ext = os.path.splitext(formatted_path)[1]
            #print(ext)
            #print(abs_file)
            if len(ext) > 0: # Has extension
                temp = formatted_path.rsplit('/',1)[0]
                #print('x:',temp)
                os.makedirs('html/'+o.hostname+temp, 0o755, exist_ok=True)
                if ext == '.html' or ext == '.htm' or ext == '.php':
                   abs_file = os.path.splitext(abs_file)[0]+str(count)+'_.php'
                   #abs_file = abs_file.replace('.php',str(count)+'_.php')
            else:
                #print(path)
                os.makedirs(path, 0o755, exist_ok=True)
                abs_file += '/index.html'
                    
            #print(abs_file)
            #print('Save file:',abs_file)
            f = codecs.open(abs_file, 'w', 'utf-8')
            f.write(raw_html)
            f.close()
            #print(frontier_q)
        except:
            print('Detect Problem => Skip this page')

#--- main process ---#

while True:
    #print('targets: ',target_urls)
    if count < WebToCrawl and index < len(target_urls):
        path = target_urls[index]
        start_crawl(path)
        index = index + 1
    else:
        break

print('Successfully download',count,'websites')

f = codecs.open('list_robots.txt', 'w', 'utf-8')
for r in robots:
    f.write(r+'\n')
f.close()
print('Save robots.txt to root directory')

f = codecs.open('list_sitemap.txt', 'w', 'utf-8')
for r in sitemap:
    f.write(r+'\n')
f.close()
print('Save list_sitemap.txt to root directory')
