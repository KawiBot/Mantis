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
        
async def setup(bot):
    await bot.add_cog(General(bot))