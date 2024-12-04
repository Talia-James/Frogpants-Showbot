#Controller GUI for the showbot_YT function. !!!! Be aware that the functionality is the same, but streamlit needs to be adapted so this script is tied to streamlit_YT_showbot.py instead !!!!
import streamlit as st
from funcs import *
import shelve
from signal import SIGTERM
from subprocess import Popen
from streamlit.runtime.scriptrunner import add_script_run_ctx,get_script_run_ctx
import psutil
from datetime import datetime
import pandas as pd




st.set_page_config(
    page_title="Temporary Frogpants Showbot GUI",
    page_icon="frogpants_logo.jpg",#, actual filepath is in navbar_components in utilities.py
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
    }
)

patreon_links = {
    'TMS':'https://www.patreon.com/tms',
    'Frogpants':'https://www.patreon.com/frogpants',
    'Brian':'https://www.patreon.com/coverville',
    'Biocow':'https://www.patreon.com/biocow',
    'Talia':'https://www.patreon.com/TaliaJames'
}

st.fragment(run_every=5)
def show_hist(df_name):
    df_toshow = pd.read_csv(f'archive/{df_name}',encoding='utf-8')
    author_col,entry_col,source_col = st.columns(3)
    with author_col:
        st.write('**Author**')
    with entry_col:
        st.write('**Title**')
    with source_col:  
        st.write('**Submitted From**')  
    for i in range(len(df_toshow)):
        author_col,entry_col,source_col = st.columns(3)
        entry = df_toshow.loc[i]
        author,title,source = entry.author,entry.title,entry.source
        with author_col:
            st.write(author)
        with entry_col:
            st.write(title)
        with source_col:
            st.write(source)
        

def main():
    streamid = False
    ctx = get_script_run_ctx(suppress_warning=True)
    with st.expander(label='StreamID',expanded=True):
        st.title('Find the stream ID')
        st.write('''
                The API needs a livechatid to be able to poll for messages and send confirmations, and to find that it needs a streamid.
                Conveniently, the streamid is the same value as videoid for API purposes, and this is easily found in the link to the stream/video.
                https://www.youtube.com/watch?v=[STREAM_ID_HERE]
                ''')
        with shelve.open('params') as f:
            if 'streamid' in f:
                streamid = f['streamid']
        st.subheader('Find streamid via channel')
        st.write("You can use my auto-detect tool to find it via your channel name instead (youtube.com/[CHANNEL_ID], defaults to yours which is @ScottJohnson). This is even easier, but it can take a few seconds longer and uses more resources. This will overwrite your previous streamid value.")
        channel = st.text_input(label='Stream ID',value='@ScottJohnson',key='chan_input')
        if st.button(label='Auto-detect'):
            streamid = find_stream_id(channel)
            if streamid:
                st.write(f'Live stream detected.\nLive stream id: {streamid}.')
                with shelve.open('params') as f:
                        f['streamid'] = streamid
                if 'streamid' not in st.session_state:
                    st.session_state['streamid']=streamid
            else:
                st.write('No live stream found.')
        st.write('Save time and bypass auto-detect to put the streamid in directly.')
        if not streamid:
            streamid_man = None
            streamid = st.text_input(label='Stream ID')
            if st.button('Save streamid'):
                with shelve.open('params') as f:
                    f['streamid'] = streamid
        else:
            if streamid:
                st.write('Saved streamid found.')
            elif 'streamid' in st.session_state:
                streamid = st.session_state['streamid']
                st.write('Cached streamid found.')
            streamid_man = st.text_input(label='Stream ID',value=streamid)
            if st.button(label='Save streamid',key='man_col_save'):
                with shelve.open('params') as f:
                        f['streamid'] = streamid_man
    with st.expander(label='Chat ID',expanded=True):
        st.title('Find chat ID')
        st.write('''
            Now with the stream ID, we can find the livechatid.
                ''')
        st.write('Click this once you have a streamid input. This interface can be janky, so once you set a variable it can help to click outside the box.')
        with shelve.open('params') as f:
            livechatid = f['livechatid']
        if livechatid:
                if 'livechatid' not in st.session_state:
                    st.session_state['livechatid'] = livechatid
        if st.button('Find chat ID'):
            try:
                livechatid = find_chat_id(streamid)
                if livechatid is not None:
                    st.write(f'Success!')
                    st.write(f'livechatid: {livechatid}')
                    st.session_state['livechatid'] = livechatid
                    with shelve.open('params') as f:
                        f['livechatid'] = livechatid
            except KeyError:
                print('No activeLiveChatId value found. The video link works, but the livestream has likely ended and thus has no active chat.')
                st.write('No activeLiveChatId value found. The video link works, but the livestream has likely ended and thus has no active chat.')      
        else:
            st.write(f'No stream detected at https://www.youtube.com/watch?v={streamid} (or the script was interacted with and re-ran without setting this value)')
        livechatid = st.text_input(label='Manual livechatid entry',value=livechatid)
        if st.button(label='Save livechatid'):
            with shelve.open('params') as f:
                f['livechatid'] = livechatid
    st.title('Spin up the bot')
    show = st.selectbox(label='Show',options=['TMS','The Monday Show'],index=0)
    if bool(os.environ['pid']) == False:
        bot_button_,quiet_button_ = st.columns(2)
        with quiet_button_:
            quiet = st.checkbox(label='Launch quietly')
        with bot_button_:
            if st.button('Launch bot.'):
                bot_args = ['python','streamlit_YT_showbot.py',livechatid,show]
                if quiet:
                    bot_args.append('quiet')
                p = Popen(bot_args)
                add_script_run_ctx(p,ctx)
                st.write(p.pid)
                os.environ['pid'] = str(p.pid)
                print(p.pid)
                st.rerun()
    else:
        pid_exists = psutil.pid_exists(int(os.environ['pid']))
        if bool(os.environ['pid']):
            if pid_exists:
                st.write('Existing process detected.')
                st.write(f'Bot Process ID: {os.environ['pid']}')
                if st.button(label='Terminate process'):
                    os.kill(int(os.environ['pid']),SIGTERM)
                    os.environ['pid']=''
                    st.write('Process terminated.')
                    if st.button('Refresh page.'):
                        st.rerun()
            else:
                st.write('Process ID found in App memory but not running on system.')
                if st.button('Click to refresh page and refresh process ID'):
                    os.environ['pid']=''
                    st.rerun()
        else:
            st.write('Previous process ID no longer active. The bot likely failed to initialize or crashed. Resetting PID.')
            print('Previous process ID no longer active. The bot likely failed to initialize or crashed. Resetting PID.')
            os.environ['pid'] = ''
            if st.button(label='Refresh page'):
                st.rerun()
    df_name = f'{show}-{datetime.today().year}-{datetime.today().month}-{datetime.today().day}.csv'

    
    with st.expander(label='Promotional Messages',expanded=False):
        st.write('Functions to send promotional messages in the chat, normally at the end of the show.') #Experimental until I confirm YouTube doesn't block a bunch of links
        if 'livechatid' in st.session_state:
            if st.button(label="Send Showbot link",key='showbot-vote-button'):
                credentials,status = build_credentials(client_secrets_file,scopes)
                if status == 'Error':
                    print('There was an error building security credentials, and the OAuth2 flow needs to be manually reauthenticated. [Send showbot link button call]')
                youtube = build_yt_obj(credentials,api_service_name, api_version,module=googleapiclient.discovery)
                request = youtube.liveChatMessages().insert(part="snippet",body={"snippet": {"liveChatId": livechatid,
                "type": "textMessageEvent",
                "textMessageDetails": {
                    "messageText": "Don't forget to vote on titles at the showbot website!"}}})
                response = request.execute()
                try:
                    sent_message = response['snippet']['displayMessage']
                    print(response)
                    print(f'Sent: {sent_message}')
                    st.write(f'Your message was successfully sent!')
                except KeyError:
                    print(response)
                    st.write(f'Something went wrong, and it looks like your message did not send correctly.')
            if st.button(label="Send relevant Patreon links.",key='patreon-button'):
                message_send = 'Support everyone on Patreon! Support TMS on the "tms" page or the Frogpants network in general on the "frogpants" page. You can find Brian under "coverville", Biocow under "biocow", and Talia under "TaliaJames".'
                #Actual links disabled until allowed from bots by Scott on his page settings, I think
                # message_raw = ['TMS is a collaborative effort! ']
                # i = 0
                # for patreon in patreon_links:
                #     i += 1
                #     link = patreon_links[patreon]
                #     if patreon == 'TMS':
                #         message = f'Support TMS directly at {link}, '
                #     elif patreon == 'Frogpants':
                #         message = f'or support the whole network at: {link}. Support individuals: '
                #     elif i == len(patreon_links):
                #         message = f' and {patreon} at {link}.'
                #     else:
                #         message = f' {patreon} at {link},'
                #     message_raw.append(message)
                # message_send = ''.join(message_raw)
                credentials,status = build_credentials(client_secrets_file,scopes)
                if status == 'Error':
                    print('There was an error building security credentials, and the OAuth2 flow needs to be manually reauthenticated. [Patreon link button call]')
                youtube = build_yt_obj(credentials,api_service_name, api_version,module=googleapiclient.discovery)
                request = youtube.liveChatMessages().insert(part="snippet",body={"snippet": {"liveChatId": livechatid,
                "type": "textMessageEvent",
                "textMessageDetails": {
                    "messageText": message_send}}})
                response = request.execute()
                try:
                    sent_message = response['snippet']['displayMessage']
                    print(f'Sent: {sent_message}')
                    st.write(f'Your message was successfully sent!')
                except KeyError:
                    st.write(f'Something went wrong, and it looks like your message did not send correctly.')
    if os.path.exists(f'archive/{df_name}'):
        st.subheader("Looks like the bot has already been active today. Here's what's already been submitted:")
        show_hist(df_name)


if __name__ == '__main__':
    if 'pid' not in os.environ:
        os.environ['pid'] = ''
    main()