import discord
from discord.ext import commands
import random
import re

class DiceRoll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="roll")
    async def roll_dice(self, ctx, *, dice_notation="1d6"):
        """
        Roll dice using standard dice notation (e.g., 2d6, 1d20).
        Usage: !roll [dice_notation]
        Default is 1d6 if no notation is provided.
        """
        # Implementation of roll command as before
        
async def setup(bot):
    await bot.add_cog(DiceRoll(bot))