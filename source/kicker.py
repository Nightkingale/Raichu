import datetime
import discord

from discord.ext import commands, tasks
from zoneinfo import ZoneInfo
from logger import create_logger


mt = ZoneInfo("US/Mountain")
time = datetime.time(hour=0, tzinfo=mt)


class Kicker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)
        self.kicker.start()


    # This doesn't actually kick anybody, but it keeps me from sitting idle.
    # I like to watch Discord streams at night as I am heading to bed. lol
    @tasks.loop(time=time)
    async def kicker(self):
        self.logger.info("The sleeping owner check has started.")
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if len(channel.members) == 1 and self.bot.owner_id == channel.members[0].id:
                    # Owner probably fell asleep in voice channel again.
                    await channel.members[0].move_to(None)
                    self.logger.info(f"{guild.owner.name} has been kicked from {channel.name}.")
                elif len(channel.members) > 1 and self.bot.owner_id == channel.members[0].id:
                    return # Owner is not alone in voice channel. End the task.


async def setup(bot: commands.Bot):
    await bot.add_cog(Kicker(bot))