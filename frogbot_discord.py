import discord
from discord.ext import commands
from funcs import *

showbot_channel,token = 'Frogpants','Nhrj6amcz4AqiSP6AVv5YhhQX8OhJ6wO'
with open('../frogbot_token.txt') as f:
    token = f.readlines()[0]

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!',intents=intents)
intents.message_content = True

author_index,submitted_titles = build_submission_history(showbot_channel)

@bot.event
async def on_ready():
    print("Let's roll, buttholes!")

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
        requests.get(submission_link)
    except TimeoutError:
        print('Timeout error')
    confirmation_message = randomize_confirmation(author,disc_format=True)
    await ctx.reply(confirmation_message)
    

    

bot.run(token)