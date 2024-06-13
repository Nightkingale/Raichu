import discord
import os

from discord.ext import commands
from json import loads
from pathlib import Path

from logger import create_logger


config = loads(Path("config.json").read_text())


class Manager(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="?",
            help_command=None,
            intents=discord.Intents.all(),
            application=983846918683770941,
            # The server name here is staying as is. Old server reference!
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


bot = Manager() # Run the bot.
bot.run(config["secrets"]["DISCORD_BOT_TOKEN"], log_handler=None)
