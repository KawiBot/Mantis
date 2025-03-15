import os
import discord
import time
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import json
import re
import datetime
from discord.ext import tasks
import aiohttp

# Load the token from our .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')

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
        # Load saved reminders
    load_reminders()
    
    # Start checking for reminders if there are any
    if any(reminders.values()):
        check_reminders.start()

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

@bot.command(name="ping")
async def ping(ctx):
    start_time = time.time()

    message = await ctx.send("Pinging...")

    end_time = time.time()

    ws_latency = round(bot.latency * 1000)
    
    msg_latency = round((end_time - start_time) * 1000)

    if ws_latency < 100:
        color = discord.Color.green()
    elif ws_latency < 200:
        color = discord.Color.gold()
    else: 
        color = discord.Color.red()

    embed = discord.Embed(
        title="🏓 Pong!",
        description="Here's my current response time:",
        color=color
    )
    embed.add_field(name="WebSocket Latency", value =f"{ws_latency}ms", inline=True)
    embed.add_field(name="Message Latency", value=f"{msg_latency}ms", inline=True)

    await message.edit(content=None, embed=embed)

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

# Dictionary to store active reminders
reminders = {}

# Function to save reminders to a file
def save_reminders():
    with open('reminders.json', 'w') as f:
        # Convert datetime objects to strings for JSON serialization
        serializable_reminders = {}
        for user_id, user_reminders in reminders.items():
            serializable_reminders[user_id] = []
            for reminder in user_reminders:
                serializable_reminder = reminder.copy()
                serializable_reminder['end_time'] = reminder['end_time'].isoformat()
                serializable_reminders[user_id].append(serializable_reminder)
        
        json.dump(serializable_reminders, f)

# Function to load reminders from a file
def load_reminders():
    global reminders
    try:
        with open('reminders.json', 'r') as f:
            serialized_reminders = json.load(f)
            
            # Convert string timestamps back to datetime objects
            for user_id, user_reminders in serialized_reminders.items():
                reminders[user_id] = []
                for reminder in user_reminders:
                    reminder['end_time'] = datetime.datetime.fromisoformat(reminder['end_time'])
                    reminders[user_id].append(reminder)
    except FileNotFoundError:
        # If the file doesn't exist yet, start with an empty dictionary
        reminders = {}

# Parse time string like "5m", "2h", "1d" into seconds
def parse_time(time_str):
    # Regular expression to match a number followed by a time unit
    match = re.match(r'(\d+)([smhdw])', time_str.lower())
    if not match:
        return None
    
    amount, unit = match.groups()
    amount = int(amount)
    
    # Convert to seconds based on the unit
    if unit == 's':  # seconds
        return amount
    elif unit == 'm':  # minutes
        return amount * 60
    elif unit == 'h':  # hours
        return amount * 3600
    elif unit == 'd':  # days
        return amount * 86400
    elif unit == 'w':  # weeks
        return amount * 604800

@bot.command(name='remindme')
async def remind_me(ctx, time_str, *, reminder_text):
    """Set a reminder. Example: !remindme 5m Take the pizza out of the oven"""
    
    # Parse the time string
    seconds = parse_time(time_str)
    if seconds is None:
        await ctx.send("Invalid time format. Use something like `5m`, `2h`, or `1d`.")
        return
    
    # Calculate when the reminder should trigger
    end_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    
    # Store the reminder
    user_id = str(ctx.author.id)
    if user_id not in reminders:
        reminders[user_id] = []
    
    reminder_data = {
        'channel_id': ctx.channel.id,
        'message': reminder_text,
        'end_time': end_time,
        'reminder_id': len(reminders[user_id])
    }
    
    reminders[user_id].append(reminder_data)
    
    # Save to file
    save_reminders()
    
    # Format a confirmation message with the reminder time
    time_str = end_time.strftime("%I:%M %p on %b %d, %Y")
    embed = discord.Embed(
        title="Reminder Confirmation",
        color=discord.Color.blue()
    )
    embed.add_field(
        name=f"I'll remind you about '{reminder_text}' at {time_str}",
        value="",
        inline=False
    )
    await ctx.send(embed=embed)
    
    # Start the reminder check task if it's not already running
    if not check_reminders.is_running():
        check_reminders.start()

@bot.command(name='myreminders')
async def list_reminders(ctx):
    """List all your active reminders"""
    user_id = str(ctx.author.id)
    
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send("You don't have any active reminders.")
        return
    
    embed = discord.Embed(
        title="Your Active Reminders",
        color=discord.Color.blue()
    )
    
    for i, reminder in enumerate(reminders[user_id]):
        time_str = reminder['end_time'].strftime("%I:%M %p on %b %d, %Y")
        embed.add_field(
            name=f"#{i+1}: Due at {time_str}",
            value=reminder['message'],
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command(name='cancelreminder')
async def cancel_reminder(ctx, reminder_num: int):
    """Cancel a reminder by its number"""
    user_id = str(ctx.author.id)
    
    # Check if the user has any reminders
    if user_id not in reminders or not reminders[user_id]:
        await ctx.send("You don't have any active reminders to cancel.")
        return
    
    # Check if the reminder number is valid
    if reminder_num <= 0 or reminder_num > len(reminders[user_id]):
        await ctx.send(f"Invalid reminder number. Use `!myreminders` to see your active reminders.")
        return
    
    # Remove the reminder
    cancelled = reminders[user_id].pop(reminder_num - 1)
    save_reminders()
    embed=discord.Embed(
        title="Cancelled Reminder",
        color=discord.Color.dark_red()
    )
    embed.add_field(
        name="",
        value=f"Your reminder:{cancelled['message']} has been cancelled!",
        inline=False
    )
    await ctx.send(embed=embed)
    # Stop the check task if there are no more reminders
    if sum(len(user_reminders) for user_reminders in reminders.values()) == 0:
        check_reminders.stop()

# Task that runs every minute to check for due reminders
@tasks.loop(seconds=30)
async def check_reminders():
    current_time = datetime.datetime.now()
    
    for user_id in list(reminders.keys()):  # Use list() to avoid dictionary size change during iteration
        if user_id in reminders:  # Double-check since we're modifying during iteration
            user_reminders = reminders[user_id]
            due_reminders = []
            
            # Find due reminders
            for i, reminder in enumerate(user_reminders):
                if current_time >= reminder['end_time']:
                    due_reminders.append((i, reminder))
            
            # Process due reminders (in reverse order to avoid index issues when removing)
            for i, reminder in sorted(due_reminders, reverse=True):
                try:
                    # Get the channel
                    channel = bot.get_channel(reminder['channel_id'])
                    if channel:
                        # Send the reminder
                        user = await bot.fetch_user(int(user_id))
                        await channel.send(f"{user.mention} Reminder: {reminder['message']}")
                    
                    # Remove this reminder
                    user_reminders.pop(i)
                except Exception as e:
                    print(f"Error sending reminder: {e}")
            
            # Remove the user from reminders if they have no more reminders
            if not user_reminders:
                del reminders[user_id]
    
    # Save updated reminders
    save_reminders()
    
    # Stop the task if there are no more reminders
    if not any(reminders.values()):
        check_reminders.stop()

@bot.command(name="google")
async def google_search(ctx, *, query):
    """Search Google and return the top results"""
    
    # Check if the API credentials are available
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        await ctx.send("The search feature is not configured properly. Please ask the bot administrator to set up Google API credentials.")
        return
    
    # Send a typing indicator to show the bot is working
    async with ctx.typing():
        try:
            # Construct the API URL
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'q': query,          # The search query
                'key': GOOGLE_API_KEY,  # Your API key
                'cx': GOOGLE_CSE_ID,    # Your search engine ID
                'num': 5             # Number of results to return (max 10)
            }
            
            # Send the request to Google
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    # Check if the request was successful
                    if response.status != 200:
                        await ctx.send(f"Error: Received status code {response.status} from Google API.")
                        return
                    
                    # Parse the JSON response
                    data = await response.json()
                    
                    # Check if there are any search results
                    if 'items' not in data:
                        await ctx.send(f"No results found for '{query}'.")
                        return
                    
                    # Create an embed to display the results
                    embed = discord.Embed(
                        title=f"Google Search Results for '{query}'",
                        color=discord.Color.blue(),
                        url=f"https://www.google.com/search?q={query.replace(' ', '+')}"
                    )
                    
                    # Add each result to the embed
                    for i, item in enumerate(data['items'], 1):
                        title = item['title']
                        link = item['link']
                        snippet = item.get('snippet', 'No description available.')
                        
                        # Add a field for this result
                        embed.add_field(
                            name=f"{i}. {title}",
                            value=f"{snippet}\n[Link]({link})",
                            inline=False
                        )
                    
                    # Send the embed
                    await ctx.send(embed=embed)
                    
        except Exception as e:
            # Handle any errors
            await ctx.send(f"An error occurred while searching: {str(e)}")
            # Print the full error for debugging
            import traceback
            traceback.print_exc()
import random

@bot.command(name="roll")
async def roll_dice(ctx, *, dice_notation="1d6"):
    """
    Roll dice using standard dice notation (e.g., 2d6, 1d20).
    Usage: !roll [dice_notation]
    Default is 1d6 if no notation is provided.
    """
    # Regular expression to match dice notation pattern (XdY)
    # X = number of dice, Y = number of sides
    dice_pattern = re.compile(r'^(\d+)d(\d+)$')
    match = dice_pattern.match(dice_notation.lower().replace(" ", ""))
    
    # Check if the provided notation is valid
    if not match:
        await ctx.send(f"Invalid dice notation. Please use the format `NdS` where N is the number of dice and S is the sides (e.g., `2d6`).")
        return
    
    # Extract the number of dice and sides
    num_dice = int(match.group(1))
    num_sides = int(match.group(2))
    
    # Set reasonable limits to prevent abuse
    if num_dice <= 0 or num_sides <= 1:
        await ctx.send("Both the number of dice and sides must be positive numbers. Sides must be at least 2.")
        return
    
    if num_dice > 100:
        await ctx.send("You can only roll up to 100 dice at once.")
        return
    
    if num_sides > 1000:
        await ctx.send("Dice cannot have more than 1000 sides.")
        return
    
    # Roll the dice
    rolls = [random.randint(1, num_sides) for _ in range(num_dice)]
    total = sum(rolls)
    
    # Create a response message
    if num_dice == 1:
        # For a single die, keep it simple
        result_message = f"🎲 You rolled a {total}"
    else:
        # For multiple dice, show individual rolls and the total
        roll_details = ' + '.join(str(r) for r in rolls)
        result_message = f"🎲 You rolled {num_dice}d{num_sides}:\n{roll_details} = **{total}**"
    
    await ctx.send(result_message)
# Run the bot with our token
bot.run(TOKEN)