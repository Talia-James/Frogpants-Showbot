import streamlit as st
from funcs import *

st.set_page_config(
    page_title="Temporary Frogpants Showbot GUI",
    page_icon="frogpants_logo.jpg",#, actual filepath is in navbar_components in utilities.py
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
    }
)

def main():
    st.title('Find the stream ID')
    st.write('''
             The API needs a livechatid to be able to poll for messages and send confirmations, and to find that it needs a streamid.
             Conveniently, the streamid is the same value as videoid for API purposes, and this is easily found in the link to the stream/video.
             https://www.youtube.com/watch?v=[STREAM_ID_HERE]
             You either manually find and enter this id, or use my auto-detect tool to find it via your channel name instead (youtube.com/[CHANNEL_ID], defaults to yours which is @ScottJohnson). This is even easier,
             but it can take a while and uses more resources than necessary for now (I haven't optimized it yet).
             ''')
    man_,auto_ = st.columns(2)
    with man_:
        st.subheader('Manual entry')
        streamid = st.text_input(label='Stream ID')
    with auto_:
        channel = st.text_input(label='Stream ID',value='@ScottJohnson')
        if st.button(label='Auto-detect'):
            streamid = find_stream_id(channel)
            if streamid:
                st.write(f'Live stream detected.\nLive stream id: {streamid}')
            else:
                st.write('No live stream found.')
    st.title('Find chat ID')
    st.write('''
        Now with the stream ID, we can find the livechatid.
            ''')
    st.write('Click this once you have a streamid input. This interface can be janky, so once you set a variable it can help to click outside the box.')
    if st.button('Find chat ID'):
        livechatid = find_chat_id(streamid)
        if livechatid is not None:
            st.write(f'Success!')
            st.write(f'livechatid: {livechatid}')

if __name__ == '__main__':
    main()
        
    
