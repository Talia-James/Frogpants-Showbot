#Controller GUI for the showbot_YT function. !!!! Be aware that the functionality is the same, but streamlit needs to be adapted so this script is tied to streamlit_YT_showbot.py instead !!!!
import streamlit as st
from funcs import *
import shelve
from streamlit_YT_showbot import bot


st.set_page_config(
    page_title="Temporary Frogpants Showbot GUI",
    page_icon="frogpants_logo.jpg",#, actual filepath is in navbar_components in utilities.py
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
    }
)

def main():
    streamid = False
    st.title('Find the stream ID')
    st.write('''
             The API needs a livechatid to be able to poll for messages and send confirmations, and to find that it needs a streamid.
             Conveniently, the streamid is the same value as videoid for API purposes, and this is easily found in the link to the stream/video.
             https://www.youtube.com/watch?v=[STREAM_ID_HERE]
             ''')
    with shelve.open('params') as f:
        if 'streamid' in f:
            streamid = f['streamid']
    with st.expander(label='Auto-detect tool'):
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
        livechatid = find_chat_id(streamid)
        if livechatid is not None:
            st.write(f'Success!')
            st.write(f'livechatid: {livechatid}')
            st.session_state['livechatid'] = livechatid
            with shelve.open('params') as f:
                f['livechatid'] = livechatid
    else:
        st.write(f'No stream detected at https://www.youtube.com/watch?v={streamid} (or the script was interacted with and re-ran without setting this value)')
    livechatid = st.text_input(label='Manual livechatid entry',value=livechatid)
    if st.button(label='Save livechatid'):
        with shelve.open('params') as f:
            f['livechatid'] = livechatid
    st.title('Spin up the bot')
    if st.button('Launch bot.'):
        bot(livechatid)
        # with shelve.open('params') as f:
        #     process = f['process']
        # if process == None:
        #     command = ['python','test.py']
        #     # output_file = "program_output.txt"
        #     # process = spm.run(command,output_file=output_file)
        #     process = Thread(target=farts,daemon=False)
        #     add_script_run_ctx(process)
        #     process.start()
        # try:
        #     for line in process.stdout:
        #         st.text(line)
        #         print(line)
        # except UnboundLocalError:
        #     st.write('Not bot output detected.')
    with st.expander(label='Experimental custom message sending'):
        st.title('Send custom message')
        st.write("While the function works fine, it's still a little experimental with how the process plays with this GUI interface package I'm using. If you send a message, the script re-runs top-down which may kill the bot background process--I'm still testing this out.")
        if 'livechatid' in st.session_state:
            message = st.text_input(label='Message text')
            if st.button(label='Send a message outside the bot loop.'):
                credentials = build_credentials(client_secrets_file,scopes)
                youtube = build_yt_obj(credentials,api_service_name, api_version,module=googleapiclient.discovery)
                request = youtube.liveChatMessages().insert(part="snippet",body={"snippet": {"liveChatId": livechatid,
                "type": "textMessageEvent",
                "textMessageDetails": {
                    "messageText": message}}})
                response = request.execute()
                try:
                    sent_message = response['snippet']['displayMessage']
                    st.write(f'Your message: {sent_message} was successfully sent!')
                except KeyError:
                    st.write(f'Something went wrong, and it looks like {message} did not send correctly.')

if __name__ == '__main__':
    main()