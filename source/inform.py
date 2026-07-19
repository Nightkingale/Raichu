import discord
import os

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
        await interaction.response.send_message("Share this link to invite people! "
            + "https://discord.gg/mYjeaZQ")
        

    @app_commands.command()
    async def ping(self, interaction: discord.Interaction):
        "Shows the bot's latency."
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong! The latency is {latency}ms.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Inform(bot))
