import aiohttp
import asyncio
import datetime
import discord

from bs4 import BeautifulSoup
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_tracks = []


    async def get_track_info(self, session, track_url):
        # Scrapes the track's page for further information.
        async with session.get(track_url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            track_name = soup.find("meta", {"property": "og:title"})["content"]
            track_duration = soup.find("meta", {"itemprop": "duration"})["content"]
            track_duration = track_duration[2:].lower().replace("h", ":").replace("m", ":").replace("s", "")
            time_element = soup.find('time').text.strip()
            time_element = datetime.datetime.strptime(time_element, "%Y-%m-%dT%H:%M:%SZ")
            track_published = time_element.strftime("%B %d, %Y %H:%M:%S")
            track_art = soup.find("meta", {"property": "og:image"})["content"]
            footer = soup.find('footer')
            purchase_link = footer.find('a')
            track_buy = purchase_link['href'] if 'http' in purchase_link['href'] else None
            return track_name, track_duration, track_published, track_art, track_buy


    def create_embed(self, track_name, track_url, author_name, author_url, author_art, track_art, track_duration, track_published, track_buy):
        # Makes a pretty embed for the track to send announcement.
        embed = discord.Embed(title=track_name, url=track_url, color=0xff7700)
        embed.set_author(name=author_name, url=author_url, icon_url=author_art)
        embed.set_thumbnail(url=track_art)
        embed.add_field(name="Duration", value=track_duration, inline=True)
        embed.add_field(name="Published", value=track_published, inline=True)
        if track_buy:
            embed.set_footer(text="Buy at: " + track_buy)
        else:
            embed.set_footer(text="No purchase link is available yet.")
        return embed


    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # SoundCLoud no longer makes their API public, so we have to scrape the website.
            async with aiohttp.ClientSession() as session:
                author_url = "https://soundcloud.com/nightkingale"
                async with session.get(author_url + "/tracks") as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    # Find the author's name and avatar.
                    author_name = soup.find("meta", {"property": "og:title"})["content"]
                    author_art = soup.find("meta", {"property": "og:image"})["content"]
                    # Find the author's tracks.
                    tracks = soup.find_all("h2", {"itemprop": "name"})
                    new_tracks = [] # A list of track URLs.
                    for track in tracks:
                        track_name = track.find("a").text
                        track_url = "https://soundcloud.com" + track.find("a")["href"]
                        new_tracks.append(track_url)
                    # Check if any tracks have been found before.
                    if not self.last_tracks:
                        self.last_tracks = new_tracks[:]
                        continue
                    # Check if any new tracks have been posted.
                    for track_url in new_tracks:
                        if track_url not in self.last_tracks:
                            self.last_tracks.append(track_url)
                            track_info = await self.get_track_info(session, track_url)
                            if track_info:
                                track_name, track_duration, track_published, track_art, track_buy = track_info
                                embed = self.create_embed(
                                    track_name, track_url, author_name, author_url, author_art,
                                    track_art, track_duration, track_published, track_buy)
                                channel = self.bot.get_channel(1127330813835485315)
                                await channel.send(f"{author_name} posted a new track on SoundCloud!", embed=embed)
            await asyncio.sleep(300)


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot), guilds=[discord.Object(id=450846070025748480)])