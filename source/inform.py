import discord
import os

from datetime import datetime
from discord import app_commands
from discord.ext import commands


class Inform(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


    @app_commands.command()
    async def build(self, interaction: discord.Interaction):
        "Shows information regarding the bot."
        embed = discord.Embed(title="Raichu", url="https://github.com/Nightkingale/Raichu",
            description="A Discord utility bot for Nightkingale Studios.", color=0xffff00)
        embed.set_author(name="Nightkingale", url="https://nightkingale.com",
            icon_url="https://avatars.githubusercontent.com/u/63483138?v=4")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/"
            + "983846918683770941/7f2ad37cee31d9599ae51a1d3082fb56.png?size=256")
        
        # Fetch commit and branch information from image if available.
        commit = os.getenv("GIT_COMMIT", "unknown")
        branch = os.getenv("GIT_BRANCH", "unknown")

        if commit != "unknown":
            embed.add_field(name="Commit", value=f"`{commit[:7]}`", inline=True)

        if branch != "unknown":
            embed.add_field(name="Branch", value=f"`{branch}`", inline=True)
        
        # Adds a footer to the embed and sends the embed.
        embed.set_footer(text="Check out my source code on GitHub!")
        await interaction.response.send_message("Here's some information about me!",
            embed=embed)


    @app_commands.command()
    async def invite(self, interaction: discord.Interaction):
        "Sends a link to an affiliated server."
        embed = discord.Embed(title="Nightkingale Studios",
            url="https://discord.nightkingale.com",
            description="The small, cozy home for development, gaming, music, and a whole lot of Wii U talk!",
            colour=0xffff00)
        embed.set_author(name="Nightkingale", url="https://nightkingale.com",
            icon_url="https://avatars.githubusercontent.com/u/63483138?v=4")
        embed.add_field(name="Official Link", value="https://discord.nightkingale.com", inline=True)
        embed.add_field(name="Direct Link", value="https://discord.gg/mYjeaZQ", inline=True)
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/450846070025748480/4dbc6b6ffa38503a1e53b7c87c38b006.webp?size=1280")
        embed.set_footer(text="Check out my source code on GitHub!")

        await interaction.response.send_message("Here's some invite links to share!", embed=embed)

    
    @app_commands.command()
    async def uptime(self, interaction: discord.Interaction):
        "Shows how long the bot has been running."
        now = datetime.datetime.now(datetime.UTC)
        uptime = now - self.bot.start_time

        total_seconds = int(uptime.total_seconds())
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(title="Nightkingale Services",
            url="https://status.nightkingale.com",
            description="You can view the health and status of all Nightkingale services on this page",
            colour=0x93bd20)
        embed.set_author(name="Nightkingale", url="https://nightkingale.com",
            icon_url="https://avatars.githubusercontent.com/u/63483138?v=4")
        embed.set_thumbnail(url="https://avatars.githubusercontent.com/u/63483138?v=4")
        embed.set_footer(text="This website is powered by Uptime Kuma, through Bell Tower.",
            icon_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRRQE8_ux9Cp6xz35xzj4U37MmBzgy9b7gXOv-DchbX9Ll25Yf900qT3sK2&s=10")
        
        await interaction.response.send_message(f"I've been running for {days} days, {hours} hours, {minutes} minutes, and "
            f"{seconds} seconds, but you can view more information on our status page!", embed=embed)


    @app_commands.command()
    async def ping(self, interaction: discord.Interaction):
        "Shows the bot's latency."
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! The latency is {latency}ms.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Inform(bot))
