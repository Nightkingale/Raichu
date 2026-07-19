import asyncio
import discord
import os

from discord.ext import commands
from json import loads
from pathlib import Path

from logger import create_logger


config = loads(Path("/data/config/config.json").read_text())


class Updater(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)
        self.updating = False

        
    # Look for new commits in the GitHub logs channel and automatically update.
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != config["channels"]["#github-logs"]:
            return  # Not the GitHub logs channel.
        
        if self.updating:
            return  # Already updating, ignore further messages.

        for embed in message.embeds:
            title = (embed.title or "").casefold()
            if "raichu" in title and "new commit" in title:
                if os.name == "posix":
                    # Run the updater service in Bell Tower. If this isn't Bell Tower, the service won't exist.
                    self.logger.info("A new commit was detected. An automatic update will be performed.")
                    self.updating = True
                    try:
                        proc = await asyncio.create_subprocess_exec(
                            "sudo", "systemctl", "start", "raichu-update.service")
                        await proc.wait()
                    finally:
                        self.updating = False
                break


async def setup(bot: commands.Bot):
    await bot.add_cog(Updater(bot))
