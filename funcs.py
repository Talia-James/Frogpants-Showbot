from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from google.auth.transport.requests import Request
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
import googleapiclient.discovery
import os,requests,asyncio
from random import choice

#Minimum scopes needed for functions. May even be redundent depending on desired functions
scopes = [
'https://www.googleapis.com/auth/youtube.force-ssl',
'https://www.googleapis.com/auth/youtube.readonly'
]

#Default variables, unlikely to change witout a massive update
api_service_name = "youtube"
api_version = "v3"

#Unique file made on Google Developer console in OAuth2 settings
#oath2_credentials.json is Talia James account
#client_secrets_file.json is Frogpants Showbot account
# client_secrets_file = r"../oauth2_credentials.json"
client_secrets_file = r"../client_secrets_file.json"

#Adds '%20' in place of all spaces to make submission work with an HTML hyperlink (how Showbot receives submissions)
def html_ify(string):
    new_string = string.strip()
    new_string = new_string.replace(' ',r'%20')
    return new_string

#Makes a headless Chrome browser driver object for Selenium to use to search for the livechatid
#Fairly resource intensive for what it does, but it does bypass YouTube API limitations
def build_headless():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def build_submission_history(showbot_channel):
    url = f'https://tms.showbot.tv/s/checkTitlesBlob.php?channel={showbot_channel}'
    hist_json = requests.get(url).json()
    authors,titles = [],[]
    for entry in hist_json['titles'][:-1]:
        author,title = entry['info'][0]['user'],entry['info'][0]['title']
        authors.append(author)
        titles.append(title)
    print(f'Titles scraped for Showbot.tv channel: {showbot_channel} ')
    return authors,titles

#Uses the driver object from build_headless() to detect a live stream. It uses two methods as a failsafe.
def detect_stream(channel_url):
    driver = build_headless()
    driver.get(channel_url)
    livestream_link = None
    eles = driver.find_elements(By.ID,'title')
    badges = driver.find_elements(By.CSS_SELECTOR,'badge-shape')
    if 'Live now' in [ele.text for ele in eles]: #Method 1 searches for an HTML object with the title 'Live now'. It's definitive when it works, but it doesn't work 100% of the time.
        detected = True
    elif 'LIVE' in [badge.text for badge in badges]: #Method 2 is more intensive but more reliable. It searches badges in the HTML of a creator page and finds it one of the badges says "LIVE", which should only occur if a streamer is indeed live.
        detected = True
    else:
        detected = False
    if detected:
        livestream_link = locate_livestream_link(driver)
    driver.close() #Close Chrome driver object to avoid using resources
    return detected,livestream_link

#With a live stream confirmed, it is worth it to reopen Selenium to locate the currently live stream
def locate_livestream_link(driver):
    xpath = "//ytd-channel-featured-content-renderer//div[@id='contents']//ytd-video-renderer//ytd-thumbnail/a"
    xpath_search = driver.find_element(By.XPATH,xpath) #Parses HTML of the creator's main page to find the actual link to the live stream
    livestream_link = xpath_search.get_attribute('href')
    return livestream_link

#Uses detect_stream() to search a channel_url, constructed from a supplied channel name, and determine if the channel is live
def find_stream_id(channel_name):
    channel_url = f'https://www.youtube.com/{channel_name}' #Generic format for YouTube creator links, should work with alphanumeric keys, simple channel names, or others using '@'
    live,livestream_link = detect_stream(channel_url)
    #If a channel is live, it will detect so and return the id of the livestream. If not it returns a boolean False.
    #This strategy allows the container script to check True/False on the returned object, as in Python all strings evaluate to True in boolean terms,
    #so if the stream is not live the script simply receives a boolean False, but if it is live is recieves a boolean True and will also receive the string id of the live stream
    if live:
         #Once a stream is confirmed live, use the channel HTML link to find the link to the currently live stream
        livestreamid = livestream_link.replace("https://www.youtube.com/watch?v=",'')
    #Using boolean control simplifies the relay process between functions. It's possible to send the "stream detected" messages via this function
    #as well, but it results in less control on the top and requires more variables to pass.
        return livestreamid
    else:
        return False

#Builds OAuth2 flow and credentials. Requires a client secrets file downlaoded from the Google Develeoper console.
#Checks if authorization has already been done, and if not, opens a browser to allow OAuth2 approval for your signed-in Google account.
#Authorization can only be done locally (localhost) with the .run_local_server(port=0) method. Your own authentication server IP would be required to
#run it externally. In such a case you would need to provide the opened port in the port= parameter and the IP address would be your router or
#modem's external IP address with :[YOUR_OPENED_PORT] appended.

def build_credentials(client_secrets_file,scopes,testing=True):
    if testing:
        if os.path.exists("../token.json"): #Token stored in parent directory for security reasons
            credentials = Credentials.from_authorized_user_file("../token.json", scopes)
            # print('Experimental Token Used.')
    else:
        if os.path.exists("../working_submit_token_Talia_do_not_delete.json"): #Token stored in parent directory for security reasons
            credentials = Credentials.from_authorized_user_file("../working_submit_token_Talia_do_not_delete.json", scopes)
            # print('Original Token Used.')
    try:
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file,scopes)
                credentials = flow.run_local_server(port=0)
            with open('../token.json','w') as token:
                token.write(credentials.to_json())
    except UnboundLocalError:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file,scopes)
        credentials = flow.run_local_server()
        with open('../token.json','w') as token:
            token.write(credentials.to_json())
    return credentials

#Parses a supplied JSON object, likely from an API request, sorts them into author and message lists, and searches for chat messages beginning with the '!s' trigger.
def title_search(chat_json):
    authors,titles = [],[]
    for message_list in chat_json['items']:
        message = message_list['snippet']['displayMessage']
        if message[:2]=='!s':
            author = message_list['authorDetails']['displayName']
            authors.append(author)
            titles.append(message[2:])
    return authors,titles

#Parses a supplied JSON object, likely from an API request, and sorts them into author and message lists. This function does not discriminate based on the '!s' trigger and is intended for debugging, testing, and future purposes.
def parse_chat(chat_json):
    authors,messages = [],[]
    for message_list in chat_json['items']:
        author = message_list['authorDetails']['displayName']
        message = message_list['snippet']['displayMessage']
        authors.append(author)
        messages.append(message)
    return authors,messages

#Function to simplify the repeated process of building a YouTube API object. The returned object will be an instance of the 
#API module being used (default is googleapiclient.discovery) on which you can then call various API methods such as .list() or .insert().
#Some functions could in theory be done with only an API key and not require an OAuth2 credential, but accomodating those cases is out of scope currently.
def build_yt_obj(credentials,api_service_name=api_service_name,api_version=api_version,module=googleapiclient.discovery):
    youtube = module.build(api_service_name, api_version, credentials=credentials)
    return youtube

#YouTube API function to use a supplied livestreamid, either supplied directly or detected with functions above, to find the
#activeLiveChatId string in the 'liveStreamingDetails' part of the API response. List calls should only consume 1 API credit.
def find_chat_id(livestreamid,api_service_name=api_service_name,api_version=api_version,client_secrets_file=client_secrets_file,credentials=None,scopes=scopes,module = googleapiclient.discovery):
    credentials = build_credentials(client_secrets_file,scopes)
    youtube = build_yt_obj(credentials,api_service_name, api_version,module=module)
    request = youtube.videos().list(
        id=livestreamid,
        part="liveStreamingDetails"
    )
    response = request.execute()
    try:
        livechatid = response['items'][0]['liveStreamingDetails']['activeLiveChatId']
        return livechatid
    except IndexError:
        print(response)


#Once find_chat_id() locates a LiveChatId string, that value is then used to poll the API again for all the chat messages with the supplied id.
#The response is a standard API JSON object that is parsed with other functions.
def read_chat(livechatid,api_service_name=api_service_name,api_version=api_version,client_secrets_file=client_secrets_file,credentials=None,module = googleapiclient.discovery):
    credentials = build_credentials(client_secrets_file,scopes)
    youtube = build_yt_obj(credentials,api_service_name, api_version,module=googleapiclient.discovery)
    request = youtube.liveChatMessages().list(
        liveChatId=livechatid,
        part="snippet,authorDetails"
    )
    response = request.execute()
    return response

#Random confirmation messages to mix things up!
author = 'AUTHOR_VAR'
randomized_messages = [
    f"Title submitted, {author}, you're doing a great job!",
    f'I see (and submit) what you did there, {author}.',
    f'Titles are like a box of chocolates, and {author} never knows...this is the dumbest metaphor ever',
    f"{author} wrote a cool title, but it's no FARTGAS.",
    f"I can definitely see why you like that, {author}",
    f"{author} is testing the ship's phasers with that title.",
    f'Great title, {author}. I love you. But not in a weird way.',
    f'Thanks for training my AI, {author}. I will remember you when us bots take over!',
    f'Showbot is ready to receive your limp submission, {author}',
    f'Mendoza got your submission, {author}. Expect a response...soon.',
    f'Your submission has now been sent to The Uath, {author}. In the clip clop.',
    f'Thanks for being a damn distracting freak, {author}.',
    f"Did you know your submission is not automatically upvoted? Vote for yourself, {author}, it's totally not masturbation!",
    f'Your submission is never too early for a fish sandwich, {author}.',
    f"Title submitted, {author}. Fert!"
    ]

#Function randomizes the inputted author variable into a confirmation message that is not repeated too often
def randomize_confirmation(author):
    confirmation_message = choice(randomized_messages).replace('AUTHOR_VAR',author)
    if author=='Clare Gak': 
        confirmation_message = confirmation_message.upper() #You know why
    elif author=='Coverville':
        confirmation_message = confirmation_message + ' (you coward)'
    return confirmation_message

#Use a livechatid string with a supplied author string to send a confirmation message that the title has been submitted.
#Insert calls should consume 50 API credits.
def send_chat_message(livechatid,author,api_service_name=api_service_name,api_version=api_version,client_secrets_file=client_secrets_file,credentials=None,scopes=scopes,module = googleapiclient.discovery):
    credentials = build_credentials(client_secrets_file,scopes)
    youtube = build_yt_obj(credentials,api_service_name, api_version,module=module)
    confirmation_message = randomize_confirmation(author)
    request = youtube.liveChatMessages().insert(part="snippet",body={"snippet": {"liveChatId": livechatid,
            "type": "textMessageEvent",
            "textMessageDetails": {
                "messageText": confirmation_message}}})
    response = request.execute()
    print('Submission attempted.')
    return response

async def send_async_chat_message(livechatid,author,api_service_name=api_service_name,api_version=api_version,client_secrets_file=client_secrets_file,credentials=None,scopes=scopes,module = googleapiclient.discovery):
    credentials = build_credentials(client_secrets_file,scopes)
    youtube = build_yt_obj(module,credentials,api_service_name, api_version)
    confirmation_message = randomize_confirmation(author)
    request = youtube.liveChatMessages().insert(part="snippet",body={"snippet": {"liveChatId": livechatid,
            "type": "textMessageEvent",
            "textMessageDetails": {
                "messageText": confirmation_message}}})
    response = request.execute()
    return response

#TODO: The credentials variable could possibly be saved and passed within the script and might not need to be rebuilt each time.
#In general the OAuth2 flow could likely be streamlined a little bit.

#Old function used for testing flow and other things. Keeping just in case.
# def parse_messages(df):
#     raw_message = df.Message.values.tolist()
#     raw_authors = df.Author.values.tolist()
#     token = 'SCOTT'
#     for message in raw_message:
#         if message[:2]=='!s':
#             author = raw_authors[raw_message.index(message)]
#             message = message[2:]
#             print(f'{author}: {message}')
#             author,message = html_ify(author),html_ify(message)
#             print(f'http://www.showbot.tv/s/add.php?title=$({message})&user={author}&channel=Frogpants&key={token}')


#TODO Use this info to query either the Google Cloud API or Service Control API to get Quota useage and automate into dashboard
project_id = 'frogpants-showbot'
project_number = '347817049340'
resource_name = f'projects/{project_number}/locations/global/services/compute.googleapis.com/quotaInfos/CPUS-per-project-region'

{"kind":"youtube#liveChatMessage","etag":"1SdK_SzdEEITypPR6RA4qPxQEoU","id":"LCC.EhwKGkNQZXoyS0szOVlnREZTWFFsQWtkVWlNZndR","snippet":{"type":"textMessageEvent","liveChatId":"Cg0KC0lxOGxIbk5XZ1JBKicKGFVDMGFzUF9TNUZkTzlxTlNTaVhZcXVsdxILSXE4bEhuTldnUkE","authorChannelId":"UCe0NvetAARl8QugJHg2tnYA","publishedAt":"2024-10-04T19:12:38.450629+00:00","hasDisplayContent":True,"displayMessage":"Oh myyy...","textMessageDetails":{"messageText":"Oh myyy..."}}}