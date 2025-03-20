import discord
from discord.ext import commands
import aiohttp
import html
import asyncio
import random
import json
import os

class Trivia(commands.Cog):
    def __init__(self, bot):
        self.self.bot = self.bot
        self.trivia_scores = {}
        self.load_scores()
    
    def load_scores(self):
        try:
            with open('data/trivia_scores.json', 'r') as f:
                self.trivia_scores = json.load(f)
        except FileNotFoundError:
            # If the file doesn't exist, start with an empty dictionary
            self.trivia_scores = {}
    
    def save_scores(self):
        # Ensure the data directory exists
        os.makedirs('data', exist_ok=True)
        
        with open('data/trivia_scores.json', 'w') as f:
            json.dump(self.trivia_scores, f)
    
    @commands.command(name="trivia")
    async def trivia(self, ctx, category="any", difficulty="medium"):
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
                    user_answer = await self.bot.wait_for('message', check=check, timeout=60.0)
                    
                    # Check if the answer is correct
                    answer_index = answer_letters.index(user_answer.content.upper())
                    
                    # Update user's score in the database
                    user_id = str(ctx.author.id)
                    if user_id not in self.bot.trivia_scores:
                        self.bot.trivia_scores[user_id] = {"correct": 0, "total": 0}
                    
                    self.bot.trivia_scores[user_id]["total"] += 1
                    
                    if answer_index == correct_index:
                        self.bot.trivia_scores[user_id]["correct"] += 1
                        
                        # Calculate the user's success rate as a percentage
                        success_rate = (self.bot.trivia_scores[user_id]["correct"] / self.bot.trivia_scores[user_id]["total"]) * 100
                        
                        await ctx.send(f"✅ Correct! The answer was {answer_letters[correct_index]}: {correct_answer}\n" 
                                      f"Your score: {self.bot.trivia_scores[user_id]['correct']}/{self.bot.trivia_scores[user_id]['total']} ({success_rate:.1f}%)")
                    else:
                        # Calculate the user's success rate as a percentage
                        success_rate = (self.bot.trivia_scores[user_id]["correct"] / self.bot.trivia_scores[user_id]["total"]) * 100
                        
                        await ctx.send(f"❌ Wrong! The correct answer was {answer_letters[correct_index]}: {correct_answer}\n"
                                      f"Your score: {self.bot.trivia_scores[user_id]['correct']}/{self.bot.trivia_scores[user_id]['total']} ({success_rate:.1f}%)")
                    
                    # Save the updated scores
                    self.save_scores()
                    
                except asyncio.TimeoutError:
                    await ctx.send(f"⏱️ Time's up! The correct answer was {answer_letters[correct_index]}: {correct_answer}")
                
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            import traceback
            traceback.print_exc()

    
       
        # Command implementation as before, but using self.trivia_scores instead of self.bot.trivia_scores
        # and self.save_scores() instead of save_scores()
        
        # For example:
        # ... rest of command code ...
        
        # Update user's score
        user_id = str(ctx.author.id)
        if user_id not in self.trivia_scores:
            self.trivia_scores[user_id] = {"correct": 0, "total": 0}
        
        self.trivia_scores[user_id]["total"] += 1
        
        if answer_index == correct_index:
            self.trivia_scores[user_id]["correct"] += 1
            # ... rest of code ...
        
        # Save scores
        self.save_scores()
    
    @commands.command(name="triviascore")
    async def trivia_score(self, ctx, user: discord.Member = None):
        """
        Check trivia scores for yourself or another user
        Usage: !triviascore [user]
        """
        if user is None:
            user = ctx.author
    
        user_id = str(user.id)
    
        if user_id not in self.bot.trivia_scores or self.bot.trivia_scores[user_id]["total"] == 0:
            await ctx.send(f"{user.display_name} hasn't answered any trivia questions yet!")
            return
    
        # Calculate statistics
        correct = self.bot.trivia_scores[user_id]["correct"]
        total = self.bot.trivia_scores[user_id]["total"]
        success_rate = (correct / total) * 100
    
        embed = discord.Embed(
            title=f"Trivia Stats for {user.display_name}",
            color=discord.Color.gold()
        )
    
        embed.add_field(name="Correct Answers", value=correct, inline=True)
        embed.add_field(name="Total Questions", value=total, inline=True)
        embed.add_field(name="Success Rate", value=f"{success_rate:.1f}%", inline=True)
    
        await ctx.send(embed=embed)
    
    @commands.command(name="triviatop")
    async def trivia_leaderboard(self, ctx):
        """
        Show the trivia leaderboard
        Usage: !triviatop
        """
        if not self.bot.trivia_scores:
            await ctx.send("No one has played trivia yet!")
            return
    
        # Sort users by correct answers
        sorted_scores = sorted(
            self.bot.trivia_scores.items(), 
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
                user = await self.bot.fetch_user(int(user_id))
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
async def setup(bot):
    await bot.add_cog(Trivia(bot))