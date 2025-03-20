import datetime
import discord
from discord.ext import commands
import time

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check the bot's response time"""
        start_time = time.time()
        message = await ctx.send("Pinging...")
        end_time = time.time()
        
        latency = round(self.bot.latency * 1000)
        api_latency = round((end_time - start_time) * 1000)
        
        embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
        embed.add_field(name="Bot Latency", value=f"{latency}ms", inline=True)
        embed.add_field(name="API Latency", value=f"{api_latency}ms", inline=True)
        
        await message.edit(content=None, embed=embed)
    
    @commands.command(name="help")
    async def help_command(self, ctx, category=None):
        """Show help information"""
        # Implementation of custom help command
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
                    "remindme":"Set a reminder. Example: !remindme 5m Take the pizza out of the oven",
                    "myreminders": "List of all your reminders.",
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
    @commands.command(name='serverinfo')
    async def server_info(self, ctx):
        guild = ctx.guild
    
        # Get owner information safely
        owner_info = "Not available"
        if guild.owner:
            owner_info = guild.owner.display_name
        else:
            if guild.owner_id:
                try:
                    owner = await guild.fetch_member(guild.owner_id)
                    if owner:
                        owner_info = owner.display_name
                except discord.errors.NotFound:
                    pass
    
        # Create the embed
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            description=f"Information about this Discord server",
            color=discord.Color.blue(),  # You can choose any color you like
            timestamp=datetime.datetime.now()  # Adds a timestamp to the embed
        )
    
        # Add server icon as thumbnail if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
    
        # Add fields for each piece of information
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=owner_info, inline=True)
        embed.add_field(name="Created On", value=guild.created_at.strftime("%B %d, %Y"),    inline=True)
    
        # Member counts
        embed.add_field(name="Total Members", value=guild.member_count, inline=True)
    
        # Try to get more detailed member counts if possible
        try:
            online_members = len([m for m in guild.members if m.status != discord.Status.   offline])
            embed.add_field(name="Online Members", value=online_members, inline=True)
        except:
            # This might fail if the bot doesn't have the members intent
            pass
    
        # Channel counts
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
    
        embed.add_field(name="Channels", value=f"{text_channels} Text | {voice_channels}    Voice | {categories} Categories", inline=True)
    
        # Role information
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    
        # Server boost information
        premium_tier = guild.premium_tier
        premium_subscriptions = guild.premium_subscription_count
        embed.add_field(name="Boost Tier", value=f"Level {premium_tier}     ({premium_subscriptions} boosts)", inline=True)
    
        # Server features
        if guild.features:
            embed.add_field(name="Server Features", value=", ".join(guild.features).replace ("_", " ").title(), inline=False)
    
        # Set footer
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.  author.display_avatar.url)
    
        # Send the embed
        await ctx.send(embed=embed)
        
async def setup(bot):
    await bot.add_cog(General(bot))