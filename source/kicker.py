import asyncio
import datetime
import discord
import pytz

from discord.ext import commands
from logger import create_logger


class Kicker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)

    # This doesn't actually kick anybody, but it keeps me from sitting idle in the voice channel.
    # I like to watch Discord streams at night as I am heading to bed. lol
    @commands.Cog.listener()
    async def on_ready(self):
        async def check_voice_channels():
            for guild in self.bot.guilds:
                self.logger.info(f"The sleeping owner check has started.")
                for channel in guild.voice_channels:
                    if len(channel.members) == 1 and guild.owner in channel.members:
                        await channel.members[0].move_to(None)
                        self.logger.info(f"{guild.owner.name} has been kicked from {channel.name}.")

        while not self.bot.is_closed():
            now = datetime.datetime.now(pytz.timezone('UTC'))
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
            seconds_until_midnight = (midnight - now).total_seconds()
            self.logger.info(f"The sleeping owner check will commence at {midnight}.")
            await asyncio.sleep(seconds_until_midnight)
            await check_voice_channels()


async def setup(bot: commands.Bot):
    await bot.add_cog(Kicker(bot), guilds=[discord.Object(id=450846070025748480)])