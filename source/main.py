import discord
import os

from discord.ext import commands
from json import loads
from logger import create_logger
from pathlib import Path


class Manager(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="r!",
            help_command=None,
            intents=discord.Intents.all(),
            application=983846918683770941,
            activity=discord.Activity(name="Nincord", type=discord.ActivityType.watching),
            status=discord.Status.online
        )
        self.logger = create_logger("Main")


    async def setup_hook(self):
        for filename in os.listdir("./source"):
            # Load all of the modules in the modules folder.
            if filename.endswith(".py") and filename not in ["main.py", "logger.py"]:
                await self.load_extension(f"{filename[:-3]}")
                self.logger.info(f"Loaded {filename} successfully from the modules folder.")


try:
    # Attempt to load the secrets from a file.
    secrets = loads(Path("secrets.json").read_text())
except FileNotFoundError:
    # This is used as a fallback when the secrets file doesn't exist.
    secrets = {"DISCORD_BOT_TOKEN": os.environ["DISCORD_BOT_TOKEN"]}


bot = Manager() # Run the bot.
bot.run(secrets["DISCORD_BOT_TOKEN"], log_handler=None)
