import discord
import os

from discord.ext import commands
from json import loads
from pathlib import Path

from logger import create_logger


config = loads(Path("config/config.json").read_text())


class Updater(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)

        
    # Look for new commits in the GitHub logs channel and automatically update.
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != config["channels"]["#github-logs"]:
            return # Not the GitHub logs channel.

        for embed in message.embeds:
            if "Raichu" in embed.title and "new commit" in embed.title:
                if os.name == "posix":
                    # Run the updater service in Area Zero. If this isn't Area Zero, the service won't exist.
                    self.logger.info("A new commit was detected. An automatic update will be performed.")
                    os.system("sudo systemctl start raichu_update.service")


async def setup(bot: commands.Bot):
    await bot.add_cog(Updater(bot))
