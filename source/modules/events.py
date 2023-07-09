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

    async def get_content(self, session, url):
        # Scrapes the content's page for further information.
        async with session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            if "soundcloud.com" in url:
                title = soup.find("meta", {"property": "og:title"})["content"]
                duration = soup.find("meta", {"itemprop": "duration"})["content"]
                published = soup.find("time")
                buy_link = soup.find("footer").find("a")
                upload_art = soup.find("meta", {"property": "og:image"})["content"]
            else:
                title = soup.find("meta", {"property": "og:title"})["content"]
                duration = soup.find("meta", {"itemprop": "duration"})["content"]
                published = soup.find("meta", itemprop="datePublished")
                author_url = soup.find("span", itemprop="author").find("link")["href"]
                upload_art = soup.find("meta", {"property": "og:image"})["content"]
                async with session.get(author_url) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    author_art = soup.find("meta", {"property": "og:image"})["content"]
            # Check if all the required elements are present.
            if title and duration and published and upload_art:
                duration = duration[2:].lower().replace("h", ":").replace("m", ":").replace("s", "")
                if "soundcloud.com" in url:
                    published = datetime.datetime.strptime(published.text.strip(), "%Y-%m-%dT%H:%M:%SZ")
                else:
                    published = datetime.datetime.strptime(published["content"], "%Y-%m-%d")
                # Convert the time element to a more readable format.
                published = published.strftime("%B %d, %Y")
                if "soundcloud.com" in url:
                    buy = buy_link["href"] if "http" in buy_link["href"] else None
                    return title, duration, published, upload_art, buy
                else:
                    return title, duration, published, upload_art, author_url, author_art

    def create_embed(self, type, title, url, author_name, author_url, author_art, art, duration=None, published=None, buy=None):
        # Makes a pretty embed for the content to send announcement.
        embed = discord.Embed(title=title, url=url)
        embed.set_author(name=author_name, url=author_url, icon_url=author_art)
        embed.set_thumbnail(url=art)
        if type == "track":
            embed.color = 0xf26f23
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Published", value=published, inline=True)
            embed.add_field(name="Purchase Link", value=buy, inline=False) if buy else None
            embed.set_footer(text="This was obtained through web scraping SoundCloud.")
        elif type == "video":
            embed.color = 0xc4302b
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Published", value=published, inline=True)
            embed.set_footer(text="This was obtained through web scraping YouTube.")
        elif type == "release":
            embed.color = 0xc4302b
            embed.description = "No further information is available for releases."
            embed.set_footer(text="This was obtained through web scraping YouTube Music.")
        return embed

    # Separate function for checking new SoundCloud tracks
    async def check_new_soundcloud_tracks(self, session, last_tracks):
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
            if not last_tracks:
                last_tracks = new_tracks[:]
                return last_tracks
            for track_url in new_tracks:
                if track_url not in last_tracks:
                    last_tracks.append(track_url)
                    track_info = await self.get_content(session, track_url)
                    if track_info:
                        track_name, track_duration, track_published, track_art, track_buy = track_info
                        embed = self.create_embed("track", track_name, track_url, author_name, author_url, author_art, track_art, track_duration, track_published, track_buy)
                        channel = self.bot.get_channel(1127330813835485315)
                        await channel.send(embed=embed)
            return last_tracks

    # Separate function for checking new YouTube videos
    async def check_new_youtube_videos(self, session, last_videos):
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
            if not last_videos:
                last_videos = new_videos[:]
                return last_videos
            for video_url in new_videos:
                if video_url not in last_videos:
                    last_videos.append(video_url)
                    video_info = await self.get_content(session, video_url)
                    if video_info:
                        video_name, video_duration, video_published, video_art, author_url, author_art = video_info
                        embed = self.create_embed("video", video_name, video_url, author_name, author_url, author_art, video_art, video_duration, video_published)
                        channel = self.bot.get_channel(1127330813835485315)
                        await channel.send(embed=embed)
            return last_videos

    # Separate function for checking new YouTube Music releases
    async def check_new_youtube_music_releases(self, session, last_releases):
        youtube_id = "UCs7Dwap3P-QK2V8PDiy-7iw"
        async with session.get("https://www.youtube.com/feeds/videos.xml?channel_id=" + youtube_id) as response:
            xml = await response.text()
            soup = BeautifulSoup(xml, "xml")
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
                if not last_releases:
                    last_releases = new_releases[:]
                    return last_releases
                for release_url, release_title, author_name, author_url, author_art, release_art in new_releases:
                    if (release_url, release_title, author_name, author_url, author_art, release_art) not in last_releases:
                        last_releases.append((release_url, release_title, author_name, author_url, author_art, release_art))
                        embed = self.create_embed("release", release_title, release_url, author_name, author_url, author_art, release_art)
                        channel = self.bot.get_channel(1127330813835485315)
                        await channel.send(embed=embed)
            return last_releases

    # Main function for the on_ready event
    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            async with aiohttp.ClientSession() as session:
                self.last_tracks = await self.check_new_soundcloud_tracks(session, self.last_tracks)
                self.last_videos = await self.check_new_youtube_videos(session, self.last_videos)
                self.last_releases = await self.check_new_youtube_music_releases(session, self.last_releases)
            await asyncio.sleep(20)


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot), guilds=[discord.Object(id=450846070025748480)])