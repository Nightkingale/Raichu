import discord
import random

from discord import app_commands
from discord.ext import commands


class Gaming(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command()


async def setup(bot: commands.Bot):
    await bot.add_cog(Gaming(bot), guilds=[discord.Object(id=450846070025748480)])
