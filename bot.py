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
# A more sophisticated help command
@bot.command(name='help')
async def help_command(ctx, category=None):
    if category is None:
        # Show categories
        categories = {
            "general": "Basic bot commands",
            "info": "Server and user information commands",
            "fun": "Entertainment commands"
        }
        
        embed = discord.Embed(
            title="Bot Help System",
            description="Use `!help [category]` to see commands in each category",
            color=discord.Color.dark_green()
        )
        
        for cat_name, cat_desc in categories.items():
            embed.add_field(name=cat_name.capitalize(), value=cat_desc, inline=False)
        
        await ctx.send(embed=embed)
    else:
        # Show commands in the specified category
        category = category.lower()
        commands_list = {
            "general": {
                "help": "Shows this help message",
                "ping": "Checks bot response time"
            },
            "info": {
                "serverinfo": "Shows information about the server",
                "userinfo": "Shows information about a user"
            },
            "fun": {
                "8ball": "Ask the magic 8-ball a question",
                "roll": "Roll a dice with specified sides"
            }
        }
        
        if category in commands_list:
            embed = discord.Embed(
                title=f"{category.capitalize()} Commands",
                color=discord.Color.blue()
            )
            
            for cmd_name, cmd_desc in commands_list[category].items():
                embed.add_field(name=f"!{cmd_name}", value=cmd_desc, inline=False)
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Category '{category}' not found. Use `!help` to see available categories.")
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use `!help` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument. Usage: `!{ctx.command.name} {ctx.command.signature}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Invalid argument type. Please check your input.")
    else:
        # Log the error for debugging
        print(f"Error in command {ctx.command}: {error}")
        await ctx.send("An error occurred while processing this command.")
# Run the bot with our token
bot.run(TOKEN)