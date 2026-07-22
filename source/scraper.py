import aiohttp
import datetime
import discord
import feedparser

from discord.ext import commands, tasks
from json import loads
from pathlib import Path

from logger import create_logger


config = loads(Path("/data/config/config.json").read_text())
scraper = loads(Path("/data/config/scraper.json").read_text())


class Scraper(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)
        self.last_videos, self.last_tracks = [], []
        self.scraper.start()


    # Makes a pretty embed for the content to send announcement.
    def create_embed(self, type, title, url, author_name, author_url, author_art,
        art, duration, published, buy=None):
        embed = discord.Embed(title=title, url=url)
        embed.set_author(name=author_name, url=author_url, icon_url=author_art)
        embed.set_thumbnail(url=art)

        if type == "video": # YouTube RSS feed
            embed.color = 0xc4302b
            if duration:
                embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Published", value=published, inline=True)
            embed.set_footer(text="This was obtained through a YouTube RSS feed.")
        elif type == "track": # SoundCloud RSS feed
            embed.color = 0xf26f23
            embed.add_field(name="Duration", value=duration, inline=True)
            embed.add_field(name="Published", value=published, inline=True)
            embed.add_field(name="Purchase Link", value=buy, inline=False) if buy else None
            embed.set_footer(text="This was obtained through a SoundCloud RSS feed.")
        return embed


    # Fetches the text content from a given URL.
    async def get_text(self, session, url):
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()


    # YouTube RSS feed checking function.
    async def check_new_youtube_videos(self, session, last_videos):
        channel_id = scraper["youtube_channel_id"]
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        feed_text = await self.get_text(session, feed_url)
        feed = feedparser.parse(feed_text)

        if not feed.entries:
            # Don't bother processing if there are no entries in the feed.
            self.logger.warning("No YouTube RSS entries were found.")
            return last_videos

        author_name = feed.feed.get("title", "YouTube")
        author_url = scraper["youtube_link"]
        author_art = scraper.get("youtube_author_art") or "https://www.youtube.com/s/desktop/6562a175/img/favicon_144x144.png"

        new_videos = [] # List to hold new video information.

        for entry in feed.entries: # Loop through each entry in the YouTube RSS feed.
            video_title = entry.get("title", "Untitled video")
            video_url = entry.get("link")
            video_id = entry.get("yt_videoid")

            if not video_url or not video_id:
                continue

            media_thumbnail = None

            # We're going to prefer the canonical media_group thumbnail if it exists.
            media_group = entry.get("media_group")
            if isinstance(media_group, list) and media_group:
                thumbnails = media_group[0].get("media_thumbnail")
                if thumbnails:
                    media_thumbnail = thumbnails[0].get("url")

            if not media_thumbnail:
                # If we made it here, we'll have to use what we can for the thumbnail.
                media_thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

            published_struct = entry.get("published_parsed")
            if published_struct:
                # Convert the published_struct to a datetime object and format it as "Month Day, Year".
                video_published = datetime.datetime(*published_struct[:6]).strftime("%B %d, %Y")
            else:
                video_published = "Unknown"

            video_info = (
                video_title,
                video_url,
                author_name,
                author_url,
                author_art,
                media_thumbnail,
                None,
                video_published,
            )
            new_videos.append(video_info)

        if not last_videos:
            # If last_videos is empty, this should be the first run.
            return [video_info[1] for video_info in new_videos]

        for video_info in new_videos:
            if video_info[1] not in last_videos:
                self.logger.info(f"A new YouTube video was found via RSS called {video_info[0]}.")
                last_videos.append(video_info[1])
                embed = self.create_embed("video", *video_info)
                channel = self.bot.get_channel(config["channels"]["#content-updates"])
                if channel:
                    await channel.send(embed=embed)

        return last_videos


    # SoundCloud RSS feed checking function.
    async def check_new_soundcloud_tracks(self, session, last_tracks):
        soundcloud_id = scraper.get("soundcloud_channel_id")
        if not soundcloud_id:
            # The config is most likely missing the SoundCloud channel ID.
            self.logger.warning("soundcloud_channel_id is missing from scraper.json.")
            return last_tracks

        feed_url = f"https://feeds.soundcloud.com/users/soundcloud:users:{soundcloud_id}/sounds.rss"
        feed_text = await self.get_text(session, feed_url)
        feed = feedparser.parse(feed_text)

        if not feed.entries:
            # Don't bother processing if there are no entries in the feed.
            self.logger.warning("No SoundCloud RSS entries were found.")
            return last_tracks

        author_name = feed.feed.get("title", "SoundCloud")
        author_url = scraper.get("soundcloud_link", "https://soundcloud.com")

        author_art = scraper.get("soundcloud_author_art")
        if not author_art:
            feed_image = feed.feed.get("image")
            if feed_image:
                author_art = feed_image.get("href") or feed_image.get("url")
        if not author_art:
            author_art = "https://a-v2.sndcdn.com/assets/images/sc-icons/favicon-2cadd14bdb.ico"

        new_tracks = [] # List to hold new track information.

        for entry in feed.entries: # Loop through each entry in the SoundCloud RSS feed.
            track_title = entry.get("title", "Untitled track")
            track_url = entry.get("link")
            if not track_url:
                continue

            track_art = None
            entry_image = entry.get("image")
            if entry_image:
                track_art = entry_image.get("href") or entry_image.get("url")

            if not track_art:
                media_thumbnail = entry.get("media_thumbnail")
                if isinstance(media_thumbnail, list) and media_thumbnail:
                    track_art = media_thumbnail[0].get("url")

            if not track_art:
                track_art = author_art

            track_duration = entry.get("itunes_duration", "Unknown")

            published_struct = entry.get("published_parsed")
            if published_struct:
                # Convert the published_struct to a datetime object and format it as "Month Day, Year".
                track_published = datetime.datetime(*published_struct[:6]).strftime("%B %d, %Y")
            else:
                track_published = "Unknown"

            track_info = (
                track_title,
                track_url,
                author_name,
                author_url,
                author_art,
                track_art,
                track_duration,
                track_published,
                None,
            )
            new_tracks.append(track_info)

        if not new_tracks:
            # If there are no new tracks, return the last_tracks list as is.
            return last_tracks

        channel = self.bot.get_channel(config["channels"]["#content-updates"])

        if not last_tracks:
            # If last_tracks is empty, this should be the first run.
            return [track_info[1] for track_info in new_tracks]

        for track_info in new_tracks:
            if track_info[1] not in last_tracks:
                self.logger.info(f"A new SoundCloud track was found via RSS called {track_info[0]}.")
                last_tracks.append(track_info[1])
                if channel:
                    embed = self.create_embed("track", *track_info)
                    await channel.send(embed=embed)

        return last_tracks
        

    # Main function for the on_ready event.
    @tasks.loop(minutes=5)
    async def scraper(self):
        async with aiohttp.ClientSession() as session:
            try:
                self.logger.info("A content polling session has started.")
                self.last_videos = await self.check_new_youtube_videos(session, self.last_videos)
                self.last_tracks = await self.check_new_soundcloud_tracks(session, self.last_tracks)
            except Exception as error:
                self.logger.error("An exception has been caught!", exc_info=error)


    @scraper.before_loop
    async def before_scraper(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Scraper(bot))