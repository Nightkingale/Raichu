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
                # Store the owner of the voice channel if they are in the channel.
                owner_id = (await self.bot.application_info()).owner.id
                owner = next((member for member in channel.members if member.id == \
                    owner_id), None)
                if owner and len(channel.members) == 1:
                    # Bot owner probably fell asleep in voice channel again.
                    await owner.move_to(None)
                    self.logger.info(f"{owner.name} has been kicked from {channel.name}.")
                elif owner:
                    return # Bot owner is not alone in voice channel. End the task.
                

async def setup(bot: commands.Bot):
    await bot.add_cog(Kicker(bot))