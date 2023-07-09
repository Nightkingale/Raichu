import aiohttp
import asyncio
import datetime
import discord
import json
import re

from bs4 import BeautifulSoup
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_tracks = []
        self.last_videos = []
        self.last_releases = []

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
            track_published = time_element.strftime("%B %d, %Y")
            track_art = soup.find("meta", {"property": "og:image"})["content"]
            footer = soup.find('footer')
            purchase_link = footer.find('a')
            track_buy = purchase_link['href'] if 'http' in purchase_link['href'] else None
            return track_name, track_duration, track_published, track_art, track_buy

    async def get_video_info(self, session, video_url):
        # Scrapes the video's page for further information.
        async with session.get(video_url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            author_url = soup.find("span", itemprop="author").find("link")["href"]
            video_name = soup.find("meta", {"property": "og:title"})["content"]
            video_duration = soup.find("meta", {"itemprop": "duration"})["content"]
            video_duration = video_duration[2:].lower().replace("h", ":").replace("m", ":").replace("s", "")
            time_element = soup.find("meta", itemprop="datePublished")["content"]
            time_element = datetime.datetime.strptime(time_element, "%Y-%m-%d")
            video_published = time_element.strftime("%B %d, %Y")
            video_art = soup.find("meta", {"property": "og:image"})["content"]
            # Scrapes the author's page for profile picture.
            async with session.get(author_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                author_art = soup.find("meta", {"property": "og:image"})["content"]
            return video_name, video_duration, video_published, video_art, author_url, author_art

    def create_track_embed(self, title, url, author_name, author_url, author_art, art, duration, published, buy):
        # Makes a pretty embed for the content to send announcement.
        embed = discord.Embed(title=title, url=url, color=0xf26f23)
        embed.set_author(name=author_name, url=author_url, icon_url=author_art)
        embed.set_thumbnail(url=art)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Published", value=published, inline=True)
        embed.add_field(name="Purchase Link", value=buy, inline=False) if buy else None
        embed.set_footer(text="This was obtained through web scraping SoundCloud.")
        return embed
    
    def create_video_embed(self, title, url, author_name, author_url, author_art, art, duration, published):
        # Makes a pretty embed for the content to send announcement.
        embed = discord.Embed(title=title, url=url, color=0xc4302b)
        embed.set_author(name=author_name, url=author_url, icon_url=author_art)
        embed.set_thumbnail(url=art)
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Published", value=published, inline=True)
        embed.set_footer(text="This was obtained through web scraping YouTube.")
        return embed
    
    def create_release_embed(self, title, url, author_name, author_url, author_art, art):
        # Makes a pretty embed for the content to send announcement.
        embed = discord.Embed(title=title, url=url, color=0xc4302b,
            description="No further information is available for releases.")
        embed.set_author(name=author_name, url=author_url, icon_url=author_art)
        embed.set_thumbnail(url=art)
        embed.set_footer(text="This was obtained through web scraping YouTube Music.")
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            # SoundCloud no longer makes their API public, so we have to scrape the website.
            async with aiohttp.ClientSession() as session:
                # Check for new SoundCloud tracks.
                author_url = "https://soundcloud.com/nightkingale"
                async with session.get(author_url + "/tracks") as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    author_name = soup.find("meta", {"property": "og:title"})["content"]
                    author_art = soup.find("meta", {"property": "og:image"})["content"]
                    tracks = soup.find_all("h2", {"itemprop": "name"})
                    new_tracks = []
                    for track in tracks:
                        track_name = track.find("a").text
                        track_url = "https://soundcloud.com" + track.find("a")["href"]
                        new_tracks.append(track_url)
                    if not self.last_tracks:
                        self.last_tracks = new_tracks[:]
                        continue
                    for track_url in new_tracks:
                        if track_url not in self.last_tracks:
                            self.last_tracks.append(track_url)
                            track_info = await self.get_track_info(session, track_url)
                            if track_info:
                                track_name, track_duration, track_published, track_art, track_buy = track_info
                                embed = self.create_track_embed(
                                    track_name, track_url, author_name, author_url, author_art,
                                    track_art, track_duration, track_published, track_buy)
                                channel = self.bot.get_channel(1127330813835485315)
                                await channel.send(embed=embed)

                # Check for new YouTube videos.
                youtube_id = "UCs7Dwap3P-QK2V8PDiy-7iw"
                async with session.get("https://www.youtube.com/feeds/videos.xml?channel_id=" + youtube_id) as response:
                    xml = await response.text()
                    soup = BeautifulSoup(xml, "xml")
                    author_name = soup.find("author").find("name").text
                    videos = soup.find_all("entry")
                    new_videos = []
                    for video in videos:
                        video_name = video.find("title").text
                        video_url = video.find("link")["href"]
                        new_videos.append(video_url)
                    if not self.last_videos:
                        self.last_videos = new_videos[:]
                        continue
                    for video_url in new_videos:
                        if video_url not in self.last_videos:
                            self.last_videos.append(video_url)
                            video_info = await self.get_video_info(session, video_url)
                            if video_info:
                                video_name, video_duration, video_published, video_art, author_url, author_art = video_info
                                embed = self.create_video_embed(
                                    video_name, video_url, author_name, author_url, author_art,
                                    video_art, video_duration, video_published)
                                channel = self.bot.get_channel(1127330813835485315)
                                await channel.send(embed=embed)
                    
                    # Check for new YouTube Music releases.
                    releases_page = soup.find("link", rel="alternate")["href"] + "/releases"
                    async with session.get(releases_page) as response:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        script = soup.find("script", text=re.compile("ytInitialData"))
                        json_text = re.search(r"ytInitialData\s*=\s*({.*?});", script.string).group(1)
                        data = json.loads(json_text)
                        releases = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][2]['tabRenderer']['content']['richGridRenderer']['contents']
                        new_releases = []
                        for release in releases:
                            video = release['richItemRenderer']['content']['playlistRenderer']
                            author_name = video['shortBylineText']['runs'][0]['text']
                            author_url = "https://www.youtube.com" + video['shortBylineText']['runs'][0]['navigationEndpoint']['browseEndpoint']['canonicalBaseUrl']
                            async with session.get(author_url) as response:
                                html = await response.text()
                                soup = BeautifulSoup(html, "html.parser")
                                author_art = soup.find("meta", {"property": "og:image"})["content"]
                            release_title = video['title']['simpleText']
                            release_art = video['thumbnails'][0]['thumbnails'][0]['url']
                            release_url = "https://www.youtube.com/watch?v=" + video['navigationEndpoint']['watchEndpoint']['videoId'] + "&list=" + video['navigationEndpoint']['watchEndpoint']['playlistId']
                            new_releases.append((release_url, release_title, author_name, author_url, author_art, release_art))
                        if not self.last_releases:
                            self.last_releases = new_releases[:]
                            continue
                        for release_url, release_title, author_name, author_url, author_art, release_art in new_releases:
                            if (release_url, release_title, author_name, author_url, author_art, release_art) not in self.last_releases:
                                self.last_releases.append((release_url, release_title, author_name, author_url, author_art, release_art))
                                embed = self.create_release_embed(release_title, release_url, author_name, author_url, author_art, release_art)
                                channel = self.bot.get_channel(1127330813835485315)
                                await channel.send(embed=embed)

            await asyncio.sleep(300)


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot), guilds=[discord.Object(id=450846070025748480)])