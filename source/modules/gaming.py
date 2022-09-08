import discord
import random

from discord import app_commands
from discord.ext import commands


class Gaming(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command()
    async def magic(self, interaction: discord.Interaction):
        "Randomly selects a response using magic."
        magic_choices = [
            "As I see it, yes.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "It is certain.",
            "It is decidedly so.",
            "Most likely.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Outlook good.",
            "Reply hazy, try again.",
            "Signs point to yes.",
            "Very doubtful.",
            "Without a doubt.",
            "Yes.",
            "Yes – definitely.",
            "You may rely on it.",
        ]

        magic_answer = random.choice(magic_choices)

        embed = discord.Embed(title="Magical Ball", color=0xffff00)
        embed.add_field(name="Prediction", value=magic_answer)

        await interaction.response.send_message("The magical ball has spoken!", embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Gaming(bot), guilds=[discord.Object(id=450846070025748480)])
