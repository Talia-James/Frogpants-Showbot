import discord,os,asyncio,sys
from discord.ext import commands
from funcs import *
from random import choice
import wordcloud
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


frogpants_channel = 'https://www.youtube.com/channel/UCIEIRz-KpYoEPnrNQuyHwJw'
showbot_channel,token = 'Frogpants','Nhrj6amcz4AqiSP6AVv5YhhQX8OhJ6wO'
url = f'https://tms.showbot.tv/'
with open('../frogbot_token.txt') as f:
    disc_token = f.readlines()[0]
global detected
detected = False

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!',intents=intents)
intents.members = True
intents.message_content = True
intents.guilds = True
intents.presences = True
intents.guild_messages = True
# print(intents)

author_index,submitted_titles = build_submission_history(showbot_channel)
bacon_gifs = os.listdir('bacon_gifs')

def get_channel(guild_id,channel_id):
    guild_obj = bot.get_guild(guild_id)
    channel_obj = guild_obj.get_channel(channel_id)
    return guild_obj,channel_obj

# async def process_detection(detected,channel,link=None):
#     if detected:
#         channel.send(f'Looks like Frogpants has gone live! Watch at: {link}')
#     else:
#         channel.send("I don't seem to be able to find a live stream for Frogpants.")

frogpants_guild_id = 146848379853471744
test_channel_id = 1308868510037839884
general_channel_id = 623339707715158016
test_server_channel = 675451203907354626
test_server_id = 675451203412295779


async def time_check(general_channel_obj,test_channel_obj,detected=False):
    if not detected:
        if datetime.now().weekday() not in [5,6]:
            hour,minute = datetime.now().hour,datetime.now().minute
            if minute<55 and minute>31:
                delta = 55 - minute
                await asyncio.sleep(delta*60)
            elif minute<30:
                delta = 30 - minute
                await asyncio.sleep(delta*60)
            else:
                detected,livestream_link = detect_stream(frogpants_channel)
                if detected and livestream_link is not None:
                    print('Stream detected.')
                    await general_channel_obj.send(f'Looks like Frogpants has gone live! Watch at: {livestream_link}')
                    await asyncio.sleep(int(60*60*2.5))
                    detected = False
                elif not detected and livestream_link is None:
                    await test_channel_obj.send('Something weird happened, and the bot automatically detected that Frogpants is live but could not retrieve the link. It will try again in one minute.')
                    await asyncio.sleep(60)
                else:
                    print('No stream detected.')
                    if minute == 55:
                        await asyncio.sleep(5*60)
                    else:
                        delta = 60-minute
                        await asyncio.sleep(delta*60)
    else:
        asyncio.sleep(3*60*60)

@bot.event
async def on_ready():
    print("Let's roll, buttholes!")
    frogpants_guild_obj,general_channel_obj = get_channel(frogpants_guild_id,general_channel_id)
    _,test_channel_obj = get_channel(frogpants_guild_id,test_channel_id)
    if frogpants_guild_obj is not None:
        print(f'Guild object found: {frogpants_guild_obj}')
    else:
        print('No guild object found.')
    if test_channel_obj is not None:
        print(f'Channel object found: {test_channel_obj}')
        if 'quiet' not in sys.argv:
            await test_channel_obj.send("Let's roll, buttholes!")
        else:
            print(f'Test channel object found: {test_channel_obj}, but quiet mode is active ergo no message will be sent.')
    else:
        print('No channel object found, no Discord message will be sent.')
    if general_channel_obj is not None:
        print('Launching and syncing live stream detection.')
        await time_check(general_channel_obj,test_channel_obj)
    else:
        print('No general channel object found, halting live stream detection.')
                    
@bot.command()
async def live(ctx):
    detected_from_command,livestream_link = detect_stream(frogpants_channel)
    if detected_from_command and livestream_link is not None:
        await time_check(None,None,True)
        await ctx.send(f'Looks like Frogpants has gone live! Watch at: {livestream_link}')
    elif not detected_from_command and livestream_link is None:
        await ctx.send('Something weird happened, and the bot command detected that Frogpants is live but could not retrieve the link.')
    else:
        ctx.send("I don't seem to be able to find a live stream for Frogpants.")

@bot.command()
async def s(ctx):
    author = ctx.message.author.display_name
    title = (ctx.message.content)[3:]
    author_index.append(author)
    submitted_titles.append(title)
    print(f'{author}: {title}') #Add new title to list and add author to another list to maintain the order. Print for debugging and monitoring purposes.
    author_html,title_html = html_ify(author),html_ify(title) #Prepare link for submission then submit via Requests module
    submission_link = f'http://www.showbot.tv/s/add.php?title={title_html}&user={author_html}&channel={showbot_channel}&key={token}'
    try:
        submission = requests.get(submission_link)
        print(submission)
        confirmation_message = randomize_confirmation(author,disc_format=True)
        await ctx.reply(confirmation_message)   
    except TimeoutError:
        print('Timeout error')

@bot.command(pass_context=True)
async def guild_info(ctx):
    guild_id = ctx.message.guild.id
    channel = ctx.message.channel.id
    guild = bot.get_guild(guild_id)
    print(guild_id)
    print(channel)
    print(guild.channels)

@bot.command()
async def showbot(ctx):
    await ctx.send(f"Don't forget to vote for titles! {url}")

@bot.command()
async def wc(ctx):
    show = 'TMS'
    df_name = f'{show}-{datetime.today().year}-{datetime.today().month}-{datetime.today().day}.csv'
    cloud_name = f'{show}-{datetime.today().year}-{datetime.today().month}-{datetime.today().day}.png'
    df = pd.read_csv(f'archive/{df_name}',encoding='utf-8')
    text = ' '.join(df.title.tolist())
    cloud = wordcloud.WordCloud().generate(text)
    cloud.to_file(f'word_clouds/{cloud_name}')
    await ctx.send(f"Word cloud of today's show titles!")
    await ctx.send(file=discord.File(f'word_clouds/{cloud_name}'))

@bot.command()
async def bacon(ctx):
    rando_gif = choice(bacon_gifs)
    gif_fp = os.path.join(os.getcwd(),'bacon_gifs',rando_gif)
    await ctx.send(file=discord.File(gif_fp))

bot.run(disc_token)