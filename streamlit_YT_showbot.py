#Current YouTube Data API request quota: 10,000 units per day.
#List functions, used to get channel/chat information and ids and also used to poll chat messages, normally cost 1 unit
#The insert function, used to send the confirmation messages, normally uses an estimated 50 units per sent message.

#Lots of processes get repeated several times, mostly for OAuth2 flow, so they've been modularized into funcs.py
from funcs import *
# import streamlit as st
# from streamlit.runtime.scriptrunner import add_script_run_ctx,get_script_run_ctx,ScriptRunner
#Requests needed to submit Showbot titles, time needed to limit API requests to stay under quota
import requests,time,sys,os
from googleapiclient.errors import HttpError
from datetime import datetime
import pandas as pd
import traceback
#Set creator page and read showbot token to prepare to submit. Default is parent directory.
print('Script Init')
showbot_channel = 'Frogpants'
livechatid = sys.argv[1]
show = sys.argv[2]
with open('../showbot_token.txt','r') as f:
    token = f.readlines()[0]
df_name = f'{show}-{datetime.today().year}-{datetime.today().month}-{datetime.today().day}.csv'
if os.path.exists(f'archive/{df_name}'):
    df = pd.read_csv(f'archive/{df_name}',encoding='utf-8')
    print('Existing df loaded')
    author_index_showbot,submitted_titles_showbot,times = build_submission_history(showbot_channel)
    new_showbot_titles,new_showbot_authors,new_showbot_times = [],[],[]
    for title,author,title_time in zip(submitted_titles_showbot,author_index_showbot,times):
        if title not in df[df.source == 'showbot'].title.tolist():
            if title[-1]=='.':
                title = title[:-1]
            new_showbot_authors.append(author)
            new_showbot_titles.append(title)
            new_showbot_times.append(title_time)
    new_df_dict = {
        'author':new_showbot_authors,
        'title':new_showbot_titles,
        'source':['showbot']*len(new_showbot_titles),
        'time':new_showbot_times
                    }
    df_to_merge = pd.DataFrame.from_dict(new_df_dict)
    df = pd.merge(df,df_to_merge,how='outer')
    author_index,submitted_titles = df.author.values.tolist(),df.title.values.tolist()
    df.to_csv(f'archive/{df_name}',encoding='utf-8',index=False)
else:
    #Scan the associated Showbot page to build a history of submissions, to prevent duplicate submissions
    #This should only run on a fresh bot boot for the day. It then goes to scrape the existing titles on showbot.
    author_index,submitted_titles,times = build_submission_history(showbot_channel)
    df = pd.DataFrame(columns=['author','title','source','time'])
    times = []
    for title in submitted_titles:
        if title[-1]=='.':
            i = submitted_titles.index(title)
            submitted_titles[i]=submitted_titles[i][:-1]
            times.append(datetime.now())
    df.author,df.title,df.source,df.time = author_index,submitted_titles,'showbot',times
    df.to_csv(f'archive/{df_name}',encoding='utf-8',index=False)



#TODO: Format everything into relevant dataframe notation. Add a source column for sanity checks vs showbot and YTbot

#livechatid is submitted in the subprocess call from the streamlit script
# livechatid = 'Cg0KC0lxOGxIbk5XZ1JBKicKGFVDMGFzUF9TNUZkTzlxTlNTaVhZcXVsdxILSXE4bEhuTldnUkE'

#Use livechatid to read chat on live stream (read_chat()) then ingest response JSON object (title_search())
#JSON objects are by default read like dictionariers in Python
#Repeat every 5 seconds to stay within API quota limit

try:
    if 'quiet' not in sys.argv:
        credentials,status = build_credentials(client_secrets_file,scopes) #Builds OAuth2 credentials object. Uses existing files or makes new one if not detected. This links the function to the account that follows the URI.
        if status == 'Error':
            print('There was an error building security credentials, and the OAuth2 flow needs to be manually reauthenticated. [Bot online announcement call]')
        youtube = build_yt_obj(credentials) #Common step in calling the API. Always have to build an object on which to call methods.
        request = youtube.liveChatMessages().insert(part="snippet",body={"snippet": {"liveChatId": livechatid,
                "type": "textMessageEvent",
                "textMessageDetails": {
                "messageText": "Showbot is up! Showbot is proudly a woke bot and was created by a Canadian trans woman."}}})
            #TODO capture and parse the response code in case the request is denied.
        response = request.execute()
    print('Loop Init')
    while True:
        authors,titles,times = title_search(read_chat(livechatid)) #Poll API for all chat messages, regardless of they've been polled already or not. title_search() already filters for '!s' chat trigger and cleans as needed
        #Check extracted titles versus previously submitted ones, submit if new
        for author,title,title_time in zip(authors,titles,times):
            if title not in submitted_titles: #Check extracted titles versus previously submitted ones, submit if new
                author_index.append(author)
                submitted_titles.append(title)
                times.append(title_time)
                print(f'{author}: {title}') #Add new title to list and add author to another list to maintain the order. Print for debugging and monitoring purposes.
                # st.write(f'{author}: {title}')
                author_html,title_html = html_ify(author),html_ify(title) #Prepare link for submission then submit via Requests module
                submission_link = f'http://www.showbot.tv/s/add.php?title={title_html}&user={author_html}&channel={showbot_channel}&key={token}'
                try:
                    requests.get(submission_link)
                    title_merge_df = pd.DataFrame(columns=['author','title','source','time'])
                    title_merge_df['author'] = [author]
                    title_merge_df['title'] = [title]
                    title_merge_df['source'] = ['YouTube']
                    title_merge_df['time'] = [title_time]
                    # title_merge_df['time'] = [datetime.now()]
                    df = pd.merge(df,title_merge_df,how='outer')
                    df.to_csv(f'archive/{df_name}',encoding='utf-8',index=False)
                except TimeoutError:
                    print(f'Timeout error while sending to showbot [{author} : {title}]')
                    pass
                #At this point the title has been submitted. This is one complete function and API call. Confirmation via the .insert() method to send a message is a separate 
                #function incurring higher quota useage.
                # try:
                response = send_chat_message(livechatid,author) #The API response in JSON format. Not technically needed but saved in case.
                # print(response)
                print(f'Title successfully submitted and confirmed: {author}.') #Generic success message only for the console for debugging and monitoring purposes.
                # except HttpError: #For some reason the script can get a 403 response code error when attempting to submit a confirmation response. This block keeps the script from halting if that occurs.
                #     print(f'HTTP Error: [{author}: {title}] submitted but failed to confirm. Likely a 403 error.')
                #     pass
                    # st.write(f'HTTP Error: [{author}: {title}] submitted but failed to confirm. Likely a 403 error.')
        time.sleep(5) #Interval at which the API is polled for all chat messages. Can be adjusted to lower costs but increase delay or vice versa.
# except HttpError:
#     # print(livechatid)
#     print(response)
#     print(f'No live chat detected via value: {livechatid}, likely because the chat has ended. The bot can safely be restarted again if you are sure the livestream is indeed live.')
#     # raise ValueError(f'No live chat detected via value: {livechatid}, likely because the chat has ended. The bot can safely be restarted again if you are sure the livestream is indeed live.')
#     # st.write(f'No live chat detected via value: {livechatid}, likely because the chat has ended. The bot can safely be restarted again if you are sure the livestream is indeed live.')
except TimeoutError:
    print('In-script timeout error. The bot can safely be restarted again.')
    os.environ['pid']=''
    # st.write('In-script timeout error. The bot can safely be restarted again.')