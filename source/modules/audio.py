import asyncio
import datetime
import discord
import youtube_dl

import json
import aiohttp
import base64
from pathlib import Path

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
    # Bind to IPv4 since IPv6 addresses cause issues.
    "source_address": "0.0.0.0",
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


class Audio(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    music_group = app_commands.Group(name="music",
        description="Commands for voice chat audio.")

    @music_group.command()
    @app_commands.describe(query="The music you would like to play.")
    async def play(self, interaction: discord.Interaction, *, query: str):
        "Plays music in the current voice channel."
        if 'https://open.spotify.com/' in query:
            self.spotify(interaction=interaction,query=query)
        else:
            if queue == []:
                queue.append(query)

            while queue != []:
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

                if not voice_client.is_playing():
                    try:
                        await interaction.response.defer()
                    except discord.errors.InteractionResponded:
                        pass

                    player = await YTDLSource.from_url(query, loop=self.bot.loop)
                    voice_client.play(player)

                    embed = discord.Embed(title=player.title, url=player.url,
                        description="Playing in " + voice_client.channel.name, color=0xffff00)
                    embed.set_author(name=player.uploader,
                        icon_url="https://cdn-icons-png.flaticon.com/512/3844/3844724.png")
                    embed.set_thumbnail(url=player.thumbnail)
                    embed.add_field(name="Duration", value=datetime.timedelta(
                        seconds=player.duration), inline=True)

                    embed.set_footer(text="This was published on " +
                        datetime.datetime.strptime(player.upload_date, "%Y%m%d").strftime("%m/%d/%Y") + "!")
                    try:
                        await interaction.followup.send("Your music is about to play!", embed=embed)
                    except discord.errors.InteractionResponded:
                        await interaction.channel.send("Your music is about to play!", embed=embed)

                    await self.bot.change_presence(activity=discord.Activity(
                        type=discord.ActivityType.listening, name=player.title))

                    while voice_client.is_playing():
                        await asyncio.sleep(1)

                    if not (len(queue) == 0 or len(queue) < 0):
                        queue.pop(0)

                    if len(queue) > 0:
                        query = queue[0]
                    else:
                        await voice_client.disconnect()
                        await self.bot.change_presence(activity=discord.Activity(
                            type=discord.ActivityType.watching, name="Nincord"))
                else:
                    await interaction.response.send_message(f"Your music, `{query}`, is added"
                        + " to the queue!")
                    return queue.append(query)

    @music_group.command()
    async def queue(self, interaction: discord.Interaction):
        "Shows the music currently waiting to be played."
        if queue == []:
            await interaction.response.send_message("There is no currently playing music!")
        else:
            voice_client = self.bot.voice_clients[0]

            embed = discord.Embed(title="Music Queue", description="Playing in "
                + voice_client.channel.name, color=0xffff00)
            embed.set_author(name=interaction.guild.name)
            embed.set_thumbnail(url=interaction.guild.icon.url)
            embed.add_field(name="Queries", value="\n".join(queue), inline=True)

            await interaction.response.send_message("Here's the current queue for"
                + " music on Nincord!", embed=embed)

    @music_group.command()
    async def skip(self, interaction: discord.Interaction):
        "Skips the current music in the voice channel."
        voice_client = interaction.guild.voice_client

        try:
            if voice_client.is_playing:
                interaction.guild.voice_client.stop()
                await interaction.response.send_message("The music has been successfully skipped!")
            else:
                await interaction.response.send_message("There is no currently playing music!")
        except AttributeError:
            await interaction.response.send_message("There is no currently playing music!")

    @music_group.command()
    async def stop(self, interaction: discord.Interaction):
        "Stops music and leaves the voice channel."
        global queue

        voice_client = interaction.guild.voice_client

        try:
            if voice_client.is_playing:
                interaction.guild.voice_client.stop()
                await voice_client.disconnect()
                await self.bot.change_presence(activity=discord.Activity(
                        type=discord.ActivityType.watching, name="Nincord"))

                queue = []

                await interaction.response.send_message("The music has been successfully stopped!")
            else:
                await interaction.response.send_message("There is no currently playing music!")
        except AttributeError:
            await interaction.response.send_message("There is no currently playing music!")

    async def spotify(self, interaction: discord.Interaction, *, query: str):

# Step 1 - Authorization 
     secrets = json.loads(Path("secrets.json").read_text())
     url = "https://accounts.spotify.com/api/token"
     headers = {}
     data = {}
     clientId = secrets["SPOTIFY_CLIENT_ID"]
     clientSecret = secrets["SPOTIFY_CLIENT_SECRET"]
     # Encode as Base64
     message = f"{clientId}:{clientSecret}"
     messageBytes = message.encode('ascii')
     base64Bytes = base64.b64encode(messageBytes)
     base64Message = base64Bytes.decode('ascii')


     headers['Authorization'] = f"Basic {base64Message}"
     data['grant_type'] = "client_credentials"

     async with self.session.get(url, headers=headers, data=data) as response:
            r = await response.json()
            token = r['access_token']

# Step 2 - Getting Query
     if '/album/' in query: # Call play in for loop with each query
          ALBUM_ID = query.split('/')[4].split('?')[0]
          ALBUM_API_URL = f'https://api.spotify.com/v1/albums/{ALBUM_ID}/tracks?market=DE'
          headers = {'accept': 'application/json', 'content-type': 'application/json', "Authorization": f'Bearer {token}'}

          async with self.session.get(ALBUM_API_URL, headers=headers) as response:
               albumJSON = await response.json()

          alb = json.dumps(albumJSON)
          tracks = json.loads(alb)

          for i in range(len(tracks["items"])):
               self.play(interaction= interaction, query = tracks["items"][i]["artists"][0]["name"] + ' - ' + tracks["items"][i]["name"])
     elif '/track/' in query: # Call play with query
          TRACK_ID = query.split('/')[4].split('?')[0]
          TRACK_API_URL = f'https://api.spotify.com/v1/tracks/{TRACK_ID}?market=de'
          headers = {'accept': 'application/json', 'content-type': 'application/json', "Authorization": f'Bearer {token}'}

          async with self.session.get(ALBUM_API_URL, headers=headers) as response:
               trackJSON = await response.json()

          track = json.dumps(trackJSON)
          trackInfo = json.loads(track)

          self.play(interaction= interaction, query = trackInfo['artists'][0]['name'] + ' - ' + trackInfo['name'])

async def setup(bot: commands.Bot):
    await bot.add_cog(Audio(bot), guilds=[discord.Object(id=450846070025748480)])
