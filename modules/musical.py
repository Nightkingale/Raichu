import asyncio
import datetime
import discord
import youtube_dl

from discord import ClientException, app_commands
from discord.ext import commands

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    "options": "-vn",
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

queue = []

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        
        self.data = data
        self.duration = data.get("duration")
        self.thumbnail = data.get("thumbnail")
        self.title = data.get("title")
        self.url = data.get("url")
        self.upload_date = data.get("upload_date")
        self.uploader = data.get("uploader")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None,
            lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename,
            **ffmpeg_options), data=data)


class Musical(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(query="The music you would like to play.")
    async def play(self, interaction: discord.Interaction, *, query: str):
        "Plays music in the current voice channel."
        if self.bot.voice_clients == []:
            try:
                channel = interaction.user.voice.channel
                voice_client = await channel.connect()
            except AttributeError:
                return await interaction.response.send_message(
                    "Please join a voice channel to use this command!")
            except ClientException:
                await interaction.guild.voice_client.disconnect()
                voice_client = await interaction.user.voice.channel.connect()
        else:
            voice_client = self.bot.voice_clients[0]
            channel = voice_client.channel

        await interaction.response.defer()

        player = await YTDLSource.from_url(query, loop=self.bot.loop)
        voice_client.play(player)

        embed = discord.Embed(title=player.title, description="Playing in "
            + str(channel), color=0xffff00)
        embed.set_author(name=player.uploader)
        embed.set_thumbnail(url=player.thumbnail)
        embed.add_field(name="Duration", value=datetime.timedelta(seconds=
            player.duration), inline=True)

        embed.set_footer(text="This was published on " +
            datetime.datetime.strptime(player.upload_date, "%Y%m%d").strftime("%m/%d/%Y") + "!")

        await interaction.followup.send("Your music is about to play!", embed=embed)
        
        while voice_client.is_playing():
            await asyncio.sleep(1)
        await voice_client.disconnect()

    @app_commands.command()
    async def stop(self, interaction: discord.Interaction):
        "Stops music and leaves the voice channel."
        voice_client = interaction.guild.voice_client

        if voice_client.is_playing or voice_client.is_paused:
            interaction.guild.voice_client.stop()
            await voice_client.disconnect()
            await interaction.response.send_message("The music has been successfully stopped!")
        else:
            await interaction.response.send_message("There is no currently playing music!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Musical(bot), guilds=[discord.Object(id=450846070025748480)])