import os
import discord
from discord.ext import commands
import config

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

# Remove default help command to create our own
bot.remove_command('help')
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
# Load all cogs from the cogs directory
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('_'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'Loaded extension: {filename[:-3]}')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} servers')
    
    # Load cogs
    await load_cogs()

# Run the bot
if __name__ == "__main__":
    bot.run(config.TOKEN)