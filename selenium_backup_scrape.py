##This is a working prototype for chat scraping without the YouTube API but requiring significantly more user intervention
#and system resources. Furthermore, it cannot send confirmation chat messages and can only submit titles. I am keeping this
#for the future in case the main script stops functioning, either from exceeding the API quota or some other reason.

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests,time
import pandas as pd
from funcs import html_ify
from selenium.common.exceptions import StaleElementReferenceException

# chrome_options = Options()
# chrome_options.add_argument("--headless=new")

driver = webdriver.Chrome()#options=chrome_options)

chat_link = "https://www.youtube.com/live_chat?continuation=0ofMyAOAARpeQ2lrcUp3b1lWVU5KUlVsU2VpMUxjRmx2UlZCdWNrNVJkWGxJZDBwM0VndHRSRUZZTmxkVlZtaERPQm9UNnFqZHVRRU5DZ3R0UkVGWU5sZFZWbWhET0NBQk1BQSUzRDABggEICAQYAiAAKACIAQGgAd_JtIqQ0IgDqAEAsgEA&dark_theme=true&authuser=0"

token = 'Nhrj6amcz4AqiSP6AVv5YhhQX8OhJ6wO'

driver.get(chat_link)
##Isolate Chat element containing all the information in the HTML
chat_record = []

while True:
    try:
        submission_links = []
        chat_container = driver.find_elements(By.TAG_NAME,'yt-live-chat-text-message-renderer')
        content_elements = [i.find_element(By.ID, 'content') for i in chat_container]
        for chat_element in content_elements:
            author = chat_element.find_element(By.ID,'author-name').text
            message = chat_element.find_element(By.ID,'message').text
            if message[:2]=='!s':
                message = message[1:]
                message_html,author_html = html_ify(message[2:]),html_ify(author)
                line = f'{author.strip()}: {message.strip()}'
                if line not in chat_record:
                    chat_record.append(line)
                    print(line)
                    submission_link = f'http://www.showbot.tv/s/add.php?title={message_html}&user={author_html}&channel=Frogpants&key={token}'
                    print(submission_link)
                    submission_links.append(submission_link)
        time.sleep(1)
        for link in submission_links:
            requests.get(link)
    except StaleElementReferenceException:
        print('Stale element error.')


    






