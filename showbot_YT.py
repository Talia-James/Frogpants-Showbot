#Standalone script that runs indepently of the streamlit controller interface
#Current YouTube Data API request quota: 10,000 units per day.
#List functions, used to get channel/chat information and ids and also used to poll chat messages, normally cost 1 unit
#The insert function, used to send the confirmation messages, normally uses an estimated 50 units per sent message.

#Lots of processes get repeated several times, mostly for OAuth2 flow, so they've been modularized into funcs.py
from funcs import *
#Requests needed to submit Showbot titles, time needed to limit API requests to stay under quota
import requests,time,sys
# from googleapiclient.errors import HttpError
#Set creator page and read showbot token to prepare to submit. Default is parent directory.
showbot_channel = 'Frogpants'
with open('../showbot_token.txt','r') as f:
    token = f.readlines()[0]


#Use selenium to see if channel is live or not.
# If the stream is live, it will return the streamid
streamid = find_stream_id('@ScottJohnson')
if streamid:
    print(f'Live stream detected.\nLive stream id: {streamid}')
else:
    print('No live stream found.')

#The streamid is needed to find the livechatid (sometimes activeLiveChatId depending on type of API request)
#While the above function is useful, it is not neded. You can easily find the streamid of any stream
#by visiting any video or live stream and looking at the URL. The streamid is the portion following the '='.
#https://www.youtube.com/watch?v=[STREAMID HERE]
#Remove the # from the line below to directly add the streamid and add #'s too all four lines above to skip the search function
#streamid = 'STREAMID'

#Use streamid to query youtube API for livechatid. Variable needs to be stored for confirmation responses
#This will error if there is no livechatid, ergo the video is likely not live or has chat disabled.
livechatid = find_chat_id(streamid)

#Scan the associated Showbot page to build a history of submissions, to prevent duplicate submissions
author_index,submitted_titles = build_submission_history(showbot_channel)

if 'quiet' in sys.argv:
    quiet = True
else:
    quiet = False
#Use livechatid to read chat on live stream (read_chat()) then ingest response JSON object (title_search())
#JSON objects are by default read like dictionaries in Python
#Repeat every 5 seconds to stay within API quota limit
try:
    if not quiet:
        credentials = build_credentials(client_secrets_file,scopes) #Builds OAuth2 credentials object. Uses existing files or makes new one if not detected. This links the function to the account that follows the URI.
        youtube = build_yt_obj(credentials) #Common step in calling the API. Always have to build an object on which to call methods.
        request = youtube.liveChatMessages().insert(part="snippet",body={"snippet": {"liveChatId": livechatid,
                "type": "textMessageEvent",
                "textMessageDetails": {
                "messageText": "Bot up. Let's roll buttholes!"}}})
        #TODO capture and parse the response code in case the request is denied.
        response = request.execute()
    print('Init')
    while True:
        authors,titles = title_search(read_chat(livechatid)) #Poll API for all chat messages, regardless of they've been polled already or not. title_search() already filters for '!s' chat trigger and cleans as needed
        #Check extracted titles versus previously submitted ones, submit if new
        for author,title in zip(authors,titles):
            if title not in submitted_titles: #Check extracted titles versus previously submitted ones, submit if new
                author_index.append(author)
                submitted_titles.append(title)
                print(f'{author}: {title}') #Add new title to list and add author to another list to maintain the order. Print for debugging and monitoring purposes.
                author_html,title_html = html_ify(author),html_ify(title) #Prepare link for submission then submit via Requests module
                submission_link = f'http://www.showbot.tv/s/add.php?title={title_html}&user={author_html}&channel={showbot_channel}&key={token}'
                try:
                    requests.get(submission_link)
                except TimeoutError:
                    print('Timeout error')
                #At this point the title has been submitted. This is one complete function and API call. Confirmation via the .insert() method to send a message is a separate 
                #function incurring higher quota useage.
                try:
                    response = send_chat_message(livechatid,author) #The API response in JSON format. Not technically needed but saved in case.
                    # delay = response['pollingIntervalMillis ']
                    print(f'Title successfully submitted and confirmed: {author}.') #Generic success message only for the console for debugging and monitoring purposes.
                except googleapiclient.errors.HttpError: #For some reason the script can get a 403 response code error when attempting to submit a confirmation response. This block keeps the script from halting if that occurs.
                    print(f'HTTP Error: [{author}: {title}] failed to submit.')
                    #This is an experimental approach to handling the 403 error by attempting to resubmit the response asynchronously.
                    #The 403 errors seemed to have stopped since making the pseudo-service account, so this may be removed in the future.
                    # print(f'HTTP Error: [{author}: {title}] failed to submit. Trying again in 3 seconds.') 
                    # asyncio.sleep(3)
                    # try:
                    #     response = asyncio.send_async_chat_message(livechatid,author)
                    # except googleapiclient.errors.HttpError:
                    #     print(f'Submission of [{author}: {title}] failed.')
                    # print(traceback.format_exc())           
        time.sleep(5) #Interval at which the API is polled for all chat messages. Can be adjusted to lower costs but increase delay or vice versa.
except googleapiclient.errors.HttpError:
    print('No live chat detected, likely because the chat has ended.')
except TimeoutError:
    print('Timeout error.')