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
                "ping": "Checks bot response time",
                "google": "Googles anything you want and returns 5 results",
                "remindme": "Sets a reminder to be notified at a later time. Example: '!remindme 5m Take pizza out of the oven'",
                "myreminders": "Returns a list of all your reminders.",
                "cancelreminder": "Allows you to cancel a reminder based on it's number."
            },
            "info": {
                "serverinfo": "Shows information about the server",
                "userinfo": "Shows information about a user"
            },
            "fun": {
                "8ball": "Ask the magic 8-ball a question",
                "roll": "Roll a dice with specified sides",
                "trivia": 
                """
                        Start a trivia question
                        Categories: general, books, film, music, theatre, tv, gaming, science, computers, math, mythology, sports, geography, history, politics, art, celebrities, animals
                        Difficulty: easy, medium, hard
                        Usage: !trivia [category] [difficulty]"""
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
import discord
from discord.ext import commands
import aiohttp
import html
import asyncio
import random
import json
import os

# Dictionary to store user scores
if not hasattr(bot, 'trivia_scores'):
    bot.trivia_scores = {}

# Function to save scores to a JSON file
def save_scores():
    with open('trivia_scores.json', 'w') as f:
        json.dump(bot.trivia_scores, f)

# Function to load scores from a JSON file
def load_scores():
    try:
        with open('trivia_scores.json', 'r') as f:
            bot.trivia_scores = json.load(f)
    except FileNotFoundError:
        bot.trivia_scores = {}

# Load scores when the bot starts
@bot.event
async def on_ready():
    # Your existing on_ready code here
    load_scores()

@bot.command(name="trivia")
async def trivia(ctx, category="any", difficulty="medium"):
    """
    Start a trivia question
    Categories: general, books, film, music, theatre, tv, gaming, science, computers, math, mythology, sports, geography, history, politics, art, celebrities, animals
    Difficulty: easy, medium, hard
    Usage: !trivia [category] [difficulty]
    """
    # Map category names to their IDs in the Open Trivia Database
    categories = {
        "any": None,
        "general": 9,
        "books": 10,
        "film": 11,
        "music": 12,
        "theatre": 13,
        "tv": 14,
        "gaming": 15,
        "science": 17,
        "computers": 18,
        "math": 19,
        "mythology": 20,
        "sports": 21,
        "geography": 22,
        "history": 23,
        "politics": 24,
        "art": 25,
        "celebrities": 26,
        "animals": 27
    }
    
    # Check if the provided category is valid
    if category.lower() not in categories:
        valid_categories = ", ".join(categories.keys())
        await ctx.send(f"⚠️ Invalid category! Valid categories are: {valid_categories}")
        return
    
    # Check if the provided difficulty is valid
    if difficulty.lower() not in ["easy", "medium", "hard"]:
        await ctx.send("⚠️ Invalid difficulty! Choose from: easy, medium, hard")
        return
    
    # Construct the API URL based on the chosen category and difficulty
    url = "https://opentdb.com/api.php?amount=1&type=multiple"
    if categories[category.lower()] is not None:
        url += f"&category={categories[category.lower()]}"
    url += f"&difficulty={difficulty.lower()}"
    
    try:
        # Fetch a question from the API
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    await ctx.send(f"⚠️ Error: The trivia API returned status code {response.status}")
                    return
                
                data = await response.json()
                
                if data["response_code"] != 0:
                    await ctx.send("⚠️ Error: Could not fetch a trivia question. Try a different category or difficulty.")
                    return
                
                # Extract question information
                question_data = data["results"][0]
                category = question_data["category"]
                difficulty = question_data["difficulty"].capitalize()
                question = html.unescape(question_data["question"])
                correct_answer = html.unescape(question_data["correct_answer"])
                
                # Get incorrect answers and add the correct answer
                answers = [html.unescape(answer) for answer in question_data["incorrect_answers"]]
                answers.append(correct_answer)
                
                # Shuffle the answers
                random.shuffle(answers)
                
                # Find the index of the correct answer
                correct_index = answers.index(correct_answer)
                
                # Create a nice embed for the question
                embed = discord.Embed(
                    title=f"Trivia Question ({difficulty})",
                    description=question,
                    color=discord.Color.blue()
                )
                
                embed.add_field(name="Category", value=category, inline=False)
                
                # Add answers as fields with letters
                answer_letters = ["A", "B", "C", "D"]
                answer_text = ""
                
                for i, answer in enumerate(answers):
                    answer_text += f"{answer_letters[i]}. {answer}\n"
                
                embed.add_field(name="Answers", value=answer_text, inline=False)
                embed.set_footer(text="Reply with the letter of your answer (A, B, C, or D)")
                
                # Send the question embed
                await ctx.send(embed=embed)
                
                # Wait for the answer from the user who requested the trivia question
                def check(message):
                    return message.author == ctx.author and message.channel == ctx.channel and message.content.upper() in answer_letters
                
                try:
                    # Wait for 30 seconds for an answer
                    user_answer = await bot.wait_for('message', check=check, timeout=60.0)
                    
                    # Check if the answer is correct
                    answer_index = answer_letters.index(user_answer.content.upper())
                    
                    # Update user's score in the database
                    user_id = str(ctx.author.id)
                    if user_id not in bot.trivia_scores:
                        bot.trivia_scores[user_id] = {"correct": 0, "total": 0}
                    
                    bot.trivia_scores[user_id]["total"] += 1
                    
                    if answer_index == correct_index:
                        bot.trivia_scores[user_id]["correct"] += 1
                        
                        # Calculate the user's success rate as a percentage
                        success_rate = (bot.trivia_scores[user_id]["correct"] / bot.trivia_scores[user_id]["total"]) * 100
                        
                        await ctx.send(f"✅ Correct! The answer was {answer_letters[correct_index]}: {correct_answer}\n" 
                                      f"Your score: {bot.trivia_scores[user_id]['correct']}/{bot.trivia_scores[user_id]['total']} ({success_rate:.1f}%)")
                    else:
                        # Calculate the user's success rate as a percentage
                        success_rate = (bot.trivia_scores[user_id]["correct"] / bot.trivia_scores[user_id]["total"]) * 100
                        
                        await ctx.send(f"❌ Wrong! The correct answer was {answer_letters[correct_index]}: {correct_answer}\n"
                                      f"Your score: {bot.trivia_scores[user_id]['correct']}/{bot.trivia_scores[user_id]['total']} ({success_rate:.1f}%)")
                    
                    # Save the updated scores
                    save_scores()
                    
                except asyncio.TimeoutError:
                    await ctx.send(f"⏱️ Time's up! The correct answer was {answer_letters[correct_index]}: {correct_answer}")
                
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

@bot.command(name="triviascore")
async def trivia_score(ctx, user: discord.Member = None):
    """
    Check trivia scores for yourself or another user
    Usage: !triviascore [user]
    """
    if user is None:
        user = ctx.author
    
    user_id = str(user.id)
    
    if user_id not in bot.trivia_scores or bot.trivia_scores[user_id]["total"] == 0:
        await ctx.send(f"{user.display_name} hasn't answered any trivia questions yet!")
        return
    
    # Calculate statistics
    correct = bot.trivia_scores[user_id]["correct"]
    total = bot.trivia_scores[user_id]["total"]
    success_rate = (correct / total) * 100
    
    embed = discord.Embed(
        title=f"Trivia Stats for {user.display_name}",
        color=discord.Color.gold()
    )
    
    embed.add_field(name="Correct Answers", value=correct, inline=True)
    embed.add_field(name="Total Questions", value=total, inline=True)
    embed.add_field(name="Success Rate", value=f"{success_rate:.1f}%", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name="triviatop")
async def trivia_leaderboard(ctx):
    """
    Show the trivia leaderboard
    Usage: !triviatop
    """
    if not bot.trivia_scores:
        await ctx.send("No one has played trivia yet!")
        return
    
    # Sort users by correct answers
    sorted_scores = sorted(
        bot.trivia_scores.items(), 
        key=lambda x: (x[1]["correct"], x[1]["correct"]/x[1]["total"] if x[1]["total"] > 0 else 0), 
        reverse=True
    )
    
    embed = discord.Embed(
        title="Trivia Leaderboard",
        description="Top trivia players",
        color=discord.Color.gold()
    )
    
    # Display the top 10 users
    for i, (user_id, score) in enumerate(sorted_scores[:10], 1):
        try:
            user = await bot.fetch_user(int(user_id))
            username = user.display_name
        except:
            username = f"User {user_id}"
        
        success_rate = (score["correct"] / score["total"]) * 100
        embed.add_field(
            name=f"{i}. {username}",
            value=f"{score['correct']}/{score['total']} ({success_rate:.1f}%)",
            inline=False
        )
    
    await ctx.send(embed=embed)
# Run the bot with our token
bot.run(TOKEN)