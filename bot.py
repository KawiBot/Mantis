import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load the token from our .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Set up our bot with necessary permissions
intents = discord.Intents.default()
intents.message_content = True  # This allows the bot to read messages
bot = commands.Bot(command_prefix='!', intents=intents)

# Remove the default help command so we can create our own
bot.remove_command('help')

# This event runs when the bot has successfully connected to Discord
@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} servers')

# A simple command that responds when a user types !hello
@bot.command(name='hello')
async def hello_command(ctx):
    await ctx.send(f'Hello, {ctx.author.mention}! I am your new bot assistant.')

# A command that shows information about the server
@bot.command(name='serverinfo')
async def server_info(ctx):
    guild = ctx.guild
    
    # Try to get owner information
    owner_info = "Not available"
    if guild.owner is not None:
        owner_info = guild.owner.display_name
    else:
        # Try to fetch owner using the owner_id
        if guild.owner_id:
            try:
                owner = await guild.fetch_member(guild.owner_id)
                if owner:
                    owner_info = owner.display_name
            except discord.errors.NotFound:
                # If we can't find the owner, keep the default message
                pass
    
    await ctx.send(f'Server Name: {guild.name}\n'
                   f'Total Members: {guild.member_count}\n'
                   f'Created At: {guild.created_at.strftime("%B %d, %Y")}\n'
                   f'Server Owner: {owner_info}')

# A fun 8ball command that gives random answers to questions
@bot.command(name='8ball')
async def eight_ball(ctx, *, question):
    import random
    responses = [
        'It is certain.',
        'Without a doubt.',
        'You may rely on it.',
        'Yes, definitely.',
        'It is decidedly so.',
        'As I see it, yes.',
        'Most likely.',
        'Yes.',
        'Signs point to yes.',
        'Reply hazy, try again.',
        'Better not tell you now.',
        'Ask again later.',
        'Cannot predict now.',
        'Concentrate and ask again.',
        'Don\'t count on it.',
        'Outlook not so good.',
        'My sources say no.',
        'Very doubtful.',
        'My reply is no.'
    ]
    await ctx.send(f'Question: {question}\nAnswer: {random.choice(responses)}')

# A command to help users understand what commands are available
@bot.command(name='help')
async def help_command(ctx):
    help_text = """
**Bot Commands**
`!hello` - Get a friendly greeting from the bot
`!serverinfo` - Display information about this server
`!8ball [question]` - Ask the magic 8-ball a question
`!help` - Show this help message
    """
    await ctx.send(help_text)

# Run the bot with our token
bot.run(TOKEN)