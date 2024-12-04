import discord,os,asyncio,sys
from discord.ext import commands
from funcs import *
from random import choice
import wordcloud
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


frogpants_channel = 'https://www.youtube.com/channel/UCIEIRz-KpYoEPnrNQuyHwJw'
showbot_channel = 'Frogpants'
with open('../showbot_token.txt',"r") as f:
    token = f.readlines()[0]
url = f'https://tms.showbot.tv/'
with open('../frogbot_token.txt',"r") as f:
    disc_token = f.readlines()[0]


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!',intents=intents)
intents.members = True
intents.message_content = True
intents.guilds = True
intents.presences = True
intents.guild_messages = True

author_index,submitted_titles,times = build_submission_history(showbot_channel)
bacon_gifs = os.listdir('bacon_gifs')

def get_channel(guild_id,channel_id):
    guild_obj = bot.get_guild(guild_id)
    channel_obj = guild_obj.get_channel(channel_id)
    return guild_obj,channel_obj

frogpants_guild_id = 146848379853471744
test_channel_id = 1308868510037839884
frogpants_general = 623339707715158016
frogpants_tms = 146848379853471744
frogpants_monday_show = 1207082163703648356
testbed_guild_id = 675451203412295779
testbed_general_id = 675451203907354626


os.environ['detected']='False'

##DON'T FORGET TO AWAIT THE SLEEP FUNCTIONS
async def time_check(channel_obj):
    while True:
        detected = os.environ['detected']
        if detected == 'False':
            print('Detected = False')
            detected,livestream_link = detect_stream(frogpants_channel)
            if detected and livestream_link is not None:
                print('Stream detected.')
                await channel_obj.send(f'Looks like Frogpants has gone live! Watch at: {livestream_link}')
                os.environ['detected'] = 'True'
            else:
                print('No stream detected.')
                print('Sleeping search for 15 minutes.')
                await asyncio.sleep(15*60)
        else:
            print('Sleeping search for 3 hours.')
            await asyncio.sleep(3*60*60)
            os.environ['detected']='False'


@bot.event
async def on_ready():
    print("Let's roll, buttholes!")
    frogpants_guild_obj,general_channel_obj = get_channel(testbed_guild_id,testbed_general_id)
    frogpants_guild_obj,test_channel_obj = get_channel(testbed_guild_id,test_channel_id)
    if frogpants_guild_obj is not None:
        print(f'Guild object found: {frogpants_guild_obj}')
    else:
        print('No guild object found.')
    if test_channel_obj is not None:
        print(f'Channel object found: {test_channel_obj}')
        if 'quiet' not in sys.argv:
            await test_channel_obj.send("Let's roll, buttholes!")
        else:
            print(f'Test channel object found: {test_channel_obj}, but quiet mode is active; ergo no message will be sent.')
    else:
        print('No channel object found, no Discord message will be sent.')
    if general_channel_obj is not None:
        print('Launching and syncing live stream detection.')
        await time_check(general_channel_obj)
    else:
        print('No general channel object found, halting live stream detection.')
                    
@bot.command()
async def live(ctx):
    detected = os.environ['detected']
    if detected == 'True':
        _,livestream_link = detect_stream(frogpants_channel)
        await ctx.send(f'Looks like Frogpants has gone live! Watch at: {livestream_link}')
    else:
        await ctx.send("I don't seem to be able to find a live stream for Frogpants.")

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