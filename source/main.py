import discord
import os

from discord.ext import commands
from json import loads
from pathlib import Path


class Manager(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="/",
            help_command=None,
            intents=discord.Intents.all(),
            application=983846918683770941
        )

    async def setup_hook(self):
        for filename in os.listdir("./source/modules"):
            if filename.endswith(".py"):
                await self.load_extension(f"modules.{filename[:-3]}")
        await bot.tree.sync(guild=discord.Object(id=450846070025748480))

    async def on_ready(self):
        activity = discord.Activity(
            name="Nincord", type=discord.ActivityType.watching)
        await bot.change_presence(activity=activity)


secrets = loads(Path("secrets.json").read_text())

bot = Manager()
bot.run(secrets["BOT_TOKEN"])
