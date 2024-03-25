from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, request
from bs4 import BeautifulSoup
import time
import random

app = Flask(__name__)

def scrape_each_publication(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # Extracting various details
    publication_title = soup.find('div', id='gsc_oci_title').text if soup.find('div', id='gsc_oci_title') else 'N/A'
    authors_div = soup.find('div', class_='gsc_oci_value')
    authors = authors_div.text.split(', ') if authors_div else []
    publication_date_div = soup.find('div', text='Publication date')
    publication_date = publication_date_div.find_next_sibling('div').text if publication_date_div else 'N/A'
    journal = soup.find('div', text='Journal').find_next_sibling('div').text if soup.find('div', text='Journal') else 'N/A'
    volume = soup.find('div', text='Volume').find_next_sibling('div').text if soup.find('div', text='Volume') else 'N/A'
    issue = soup.find('div', text='Issue').find_next_sibling('div').text if soup.find('div', text='Issue') else 'N/A'
    pages = soup.find('div', text='Pages').find_next_sibling('div').text if soup.find('div', text='Pages') else 'N/A'
    publisher = soup.find('div', text='Publisher').find_next_sibling('div').text if soup.find('div', text='Publisher') else 'N/A'
    description = soup.find('div', id='gsc_oci_descr').text if soup.find('div', id='gsc_oci_descr') else 'N/A'
    total_citations_container = soup.find('div', text='Total citations').find_next_sibling('div')
    if total_citations_container:
        total_citations_link = total_citations_container.find('a')
        total_citations = total_citations_link.text if total_citations_link else 'N/A'
    else:
        total_citations = 'N/A'

    citations_year_wise = []
    citation_bars = soup.select('#gsc_oci_graph_bars .gsc_oci_g_t')
    citation_counts = soup.select('#gsc_oci_graph_bars .gsc_oci_g_a')

    for year, count in zip(citation_bars, citation_counts):
        year_text = year.text.strip()
        count_text = count.text.strip()
        citations_year_wise.append({year_text: count_text})

    
    # Extracting scholar articles
    scholar_articles = []
    scholar_articles_div = soup.find_all('div', class_='gsc_oci_merged_snippet')
    for article in scholar_articles_div:
        title = article.find('a').text if article.find('a') else 'N/A'
        scholar_articles.append(title)

    return {
        'title' : publication_title,
        'authors': authors,
        'publication_date': publication_date,
        'journal': journal,
        'volume': volume,
        'issue': issue,
        'pages': pages,
        'publisher': publisher,
        'description': description,
        'citations': {"total_citations" : total_citations, "year_wise_citations" : citations_year_wise},
        'scholar_articles': scholar_articles
    }





def download_selenium():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver




def populate_complete_publication_list(driver):
    while True:
        try:
            show_more_button = driver.find_element(By.ID, "gsc_bpf_more")
            if show_more_button.get_attribute('disabled'):
                break
            show_more_button.click()
            time.sleep(2)
        except Exception as e:
            break


def get_all_publication_title_with_url(driver):
    title_elements = driver.find_elements(By.CSS_SELECTOR, ".gsc_a_tr .gsc_a_at")
    titles_urls = [(title.get_attribute('textContent'), title.get_attribute('href')) for title in title_elements]
    return titles_urls

def get_each_publication_data(driver, titles_urls):
    all_data = []
    count = 0
    for title, url in titles_urls:
        count = count + 1
        if (count > 2) :
            break
        driver.get(url)
        details = scrape_each_publication(driver)
        all_data.append(details)
        driver.back()
    return all_data

def get_random_proxy():
    with open("valid_proxy.txt", "r") as file:
        proxies = file.read().split("\n")
        return random.choice(proxies)


@app.route("/health", methods=["GET"])
def healthCheck():
    return "App is working"


@app.route("/scrap/publications", methods=['POST'])
def scrap_publications():
    data = request.get_json()
    scrapped_data = []
    for url in data['url']:
        while True:
            driver = download_selenium()
            test = driver.get(url)
            populate_complete_publication_list(driver)
            titles_urls = get_all_publication_title_with_url(driver)
            data = get_each_publication_data(driver, titles_urls)
            page_title = driver.title.split("-")[0].strip()
            scrapped_data.append({page_title : data})
            driver.quit()
            break
    return scrapped_data

if __name__ == "__main__":
    app.run(host="0.0.0.0")
