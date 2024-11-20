import discord,os,asyncio
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

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!',intents=intents)
intents.message_content = True

author_index,submitted_titles = build_submission_history(showbot_channel)
bacon_gifs = os.listdir('bacon_gifs')

@bot.event
async def on_ready():
    print("Let's roll, buttholes!")

@bot.command()
async def live(ctx):
    detected,livestream_link = detect_stream(frogpants_channel)
    if detected:
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