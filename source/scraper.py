import aiohttp
import datetime
import discord
import re

from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from json import loads
from pathlib import Path

from logger import create_logger


config = loads(Path("config/config.json").read_text())
scraper = loads(Path("config/scraper.json").read_text())


class Scraper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)
        self.last_tracks, self.last_videos, self.last_releases = [], [], []
        self.scraper.start()


    def create_embed(self, type, title, url, author_name, author_url, author_art,
        art, duration, published, buy=None):
        # Makes a pretty embed for the content to send announcement.
        embed = discord.Embed(title=title, url=url)
        embed.set_author(name=author_name, url=author_url, icon_url=author_art)
        embed.set_thumbnail(url=art)

        if type == "track":
            embed.color = 0xf26f23 # SoundCloud service
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Published", value=published, inline=True)
            embed.add_field(name="Purchase Link", value=buy, inline=False) if buy else None
            embed.set_footer(text="This was obtained through web scraping SoundCloud.")
        elif type == "video":
            embed.color = 0xc4302b # YouTube service
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Published", value=published, inline=True)
            embed.set_footer(text="This was obtained through web scraping YouTube.")
        elif type == "release":
            embed.color = 0xc4302b # YouTube Music service
            embed.add_field(name="Tracks", value=duration, inline=True)
            embed.add_field(name="Published", value=published, inline=True)
            embed.set_footer(text="This was obtained through web scraping YouTube Music.")
        return embed


    # Separate function for checking new SoundCloud tracks.
    async def check_new_soundcloud_tracks(self, session, last_tracks):
        author_url = scraper["soundcloud_link"]
        async with session.get(author_url + "/tracks") as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # Scrapes the author's name, art, and track list.
            author_name = soup.find("meta", {"property": "og:title"})["content"]
            author_art = soup.find("meta", {"property": "og:image"})["content"]
            tracks = soup.find_all("h2", {"itemprop": "name"})
            new_tracks = []

            for track in tracks:
                # Get the track's information.
                track_url = "https://soundcloud.com" + track.find("a")["href"]
                async with session.get(track_url) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    title = soup.find("meta", {"property": "og:title"})["content"]
                    duration = soup.find("meta", {"itemprop": "duration"})["content"]
                    duration = duration[2:].lower().replace("h", ":").replace("m", ":").replace("s", "")
                    published = soup.find("time")
                    published = datetime.datetime.strptime(published.text.strip(), "%Y-%m-%dT%H:%M:%SZ")
                    published = published.strftime("%B %d, %Y")
                    buy_link = soup.find("footer").find("a")["href"] if soup.find("footer").find("a") else None
                    if buy_link and "http" not in buy_link:
                        buy_link = None # No valid link found.
                    upload_art = soup.find("meta", {"property": "og:image"})["content"]
                track_info = (title, track_url, author_name, author_url, author_art, upload_art,
                    duration, published, buy_link)
                new_tracks.append(track_info)

            # Check if the held data is empty.
            if not last_tracks:
                last_tracks = [track_info[1] for track_info in new_tracks]
                return last_tracks
            
            for track_info in new_tracks:
                # Compare to see if the exact data is already posted.
                if track_info[1] not in last_tracks:
                    self.logger.info(f"A new SoundCloud track was scraped called {track_info[0]}.")
                    last_tracks.append(track_info[1])
                    embed = self.create_embed("track", *track_info)
                    channel = self.bot.get_channel(config["channels"]["#content-updates"])
                    await channel.send(embed=embed)

        return last_tracks


    # Separate function for checking new YouTube videos.
    async def check_new_youtube_videos(self, session, last_videos):
        author_url = scraper["youtube_link"]
        async with session.get(author_url + "/videos") as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")

            # Grab the JSON data from the page.
            script = soup.find("script", text=re.compile("ytInitialData"))
            json_text = re.search(r"ytInitialData\s*=\s*({.*?});", script.string).group(1)
            data = loads(json_text)

            # Grab the list of videos from the scraped JSON data.
            videos = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][1]['tabRenderer'] \
                ['content']['richGridRenderer']['contents']
            
            # Scrape the author name and art from the page.
            author_name = soup.find("meta", {"property": "og:title"})["content"]
            author_art = soup.find("meta", {"property": "og:image"})["content"]
            new_videos = []

            for video in videos:
                # Loop through the videos and grab individual data.
                video = video['richItemRenderer']['content']['videoRenderer']
                video_title = video['title']['runs'][0]['text']
                video_art = video['thumbnail']['thumbnails'][0]['url']
                video_url = "https://www.youtube.com/watch?v=" + video['navigationEndpoint'] \
                    ['watchEndpoint']['videoId']
                video_duration = video['lengthText']['simpleText']
                async with session.get(video_url) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    video_published_tag = soup.find("meta", {"itemprop": "datePublished"})
                    if video_published_tag and video_published_tag.get("content"):
                        video_published = datetime.datetime.strptime(video_published_tag["content"], \
                            "%Y-%m-%dT%H:%M:%S%z")
                        video_published = video_published.strftime("%B %d, %Y")
                    else:
                        video_published = "Unknown"
                video_info = (video_title, video_url, author_name, author_url, author_art, video_art,
                    video_duration, video_published)
                new_videos.append(video_info)

            # Check if the held data is empty.
            if not last_videos:
                last_videos = [video_info[1] for video_info in new_videos]
                return last_videos
            
            for video_info in new_videos:
                if video_info[1] not in last_videos:
                    self.logger.info(f"A new YouTube video was scraped called {video_info[0]}.")
                    last_videos.append(video_info[1])
                    embed = self.create_embed("video", *video_info)
                    channel = self.bot.get_channel(config["channels"]["#content-updates"])
                    await channel.send(embed=embed)

        return last_videos


    # Separate function for checking new YouTube Music releases.
    async def check_new_youtube_music_releases(self, session, last_releases):
        author_url = scraper["youtube_link"]
        async with session.get(author_url + "/releases") as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # Grab the JSON data from the page.
            script = soup.find("script", text=re.compile("ytInitialData"))
            json_text = re.search(r"ytInitialData\s*=\s*({.*?});", script.string).group(1)
            data = loads(json_text)

            # Grab the list of releases from scraped JSON data.
            releases = data['contents']['twoColumnBrowseResultsRenderer']['tabs'][3]['tabRenderer'] \
                ['content']['richGridRenderer']['contents']
            
            # Scrape the author name and art from the page.
            author_name = soup.find("meta", {"property": "og:title"})["content"]
            author_art = soup.find("meta", {"property": "og:image"})["content"]
            new_releases = []

            for release in releases:
                # Loop through the releases and grab individual data.
                video = release['richItemRenderer']['content']['playlistRenderer']
                release_title = video['title']['simpleText']
                release_art = video['thumbnails'][0]['thumbnails'][0]['url']
                track_count = video['videoCount']
                release_url = "https://www.youtube.com/watch?v=" + video['navigationEndpoint'] \
                    ['watchEndpoint']['videoId'] + "&list=" + video['navigationEndpoint'] \
                    ['watchEndpoint']['playlistId']
                async with session.get(release_url) as response:
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    release_published_tag = soup.find("meta", {"itemprop": "datePublished"})
                    if release_published_tag and release_published_tag.get("content"):
                        release_published = datetime.datetime.strptime(release_published_tag["content"], \
                            "%Y-%m-%dT%H:%M:%S%z")
                        release_published = release_published.strftime("%B %d, %Y")
                    else:
                        release_published = "Unknown"
                release_info = (release_title, release_url, author_name, author_url, author_art,
                    release_art, track_count, release_published)
                new_releases.append(release_info)

            # Check if the held data is empty.
            if not last_releases:
                last_releases = [release_info[1] for release_info in new_releases]
                return last_releases
            
            for release_info in new_releases:
                # Compare to see if the exact data already was posted.
                if release_info[1] not in last_releases:
                    self.logger.info(f"A new YouTube Music release was scraped called {release_info[0]}")
                    last_releases.append(release_info[1])
                    embed = self.create_embed("release", *release_info)
                    channel = self.bot.get_channel(config["channels"]["#content-updates"])
                    await channel.send(embed=embed)

            return last_releases


    # Main function for the on_ready event
    @tasks.loop(minutes=5)
    async def scraper(self):
        async with aiohttp.ClientSession() as session:
            try:
                self.logger.info("A web scraping session has started.")
                self.last_tracks = await self.check_new_soundcloud_tracks(session, self.last_tracks)
                self.last_videos = await self.check_new_youtube_videos(session, self.last_videos)
                self.last_releases = await self.check_new_youtube_music_releases(session, self.last_releases)
            except Exception as error:
                self.logger.error(f"An exception has been caught!", exc_info=error)


async def setup(bot: commands.Bot):
    await bot.add_cog(Scraper(bot))