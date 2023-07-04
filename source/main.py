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
            # Load all of the modules in the modules folder.
            if filename.endswith(".py"):
                await self.load_extension(f"modules.{filename[:-3]}")
        # Sync the commands to the Discord bot's tree.
        await bot.tree.sync()
        await bot.tree.sync(guild=discord.Object(id=450846070025748480))


    async def on_ready(self):
        # Set the bot's activity.
        activity = discord.Activity(
            name="Nincord", type=discord.ActivityType.watching)
        await bot.change_presence(activity=activity)


try:
    # Attempt to load the secrets from a file.
    secrets = loads(Path("secrets.json").read_text())
except FileNotFoundError:
    # This is used as a fallback when the secrets file doesn't exist.
    secrets = {"DISCORD_BOT_TOKEN": os.environ["DISCORD_BOT_TOKEN"]}

bot = Manager() # Run the bot.
bot.run(secrets["DISCORD_BOT_TOKEN"])
