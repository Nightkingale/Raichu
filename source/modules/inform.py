import discord
import subprocess

from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from subprocess import check_output


class Inform(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    inform_group = app_commands.Group(name="inform",
        description="Commands for miscellaneous information.")


    @inform_group.command()
    async def build(self, interaction: discord.Interaction):
        "Shows information regarding the bot."
        embed = discord.Embed(title="Raichu", url="https://github.com/Nightkingale/Raichu",
            description="A Discord utility bot for Nincord.", color=0xffff00)
        embed.set_author(name="Nightkingale", url="https://nightkingale.com",
            icon_url="https://avatars.githubusercontent.com/u/63483138?v=4")
        embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/"
            + "983846918683770941/7f2ad37cee31d9599ae51a1d3082fb56.png?size=256")
        # Adds the commit hash to the embed.
        try:
            # Fetches the commit hash from the git repository.
            commit = check_output(
                ["git", "rev-parse", "HEAD"]).decode("ascii")[:-1]
            embed.add_field(name="Commit", value="`" + commit[0:7] + "`", inline=True)
        except subprocess.CalledProcessError:
            pass
        # Adds the branch name to the embed.
        try:
            # Fetches the branch name from the git repository.
            branch = check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode()[:-1]
            embed.add_field(name="Branch", value="`" + branch + "`", inline=True)
        except subprocess.CalledProcessError:
            pass
        # Adds a footer to the embed and sends the embed.
        embed.set_footer(text="Check out my source code on GitHub!")
        await interaction.response.send_message("Here's some information about me!",
            embed=embed)


    @inform_group.command()
    @app_commands.choices(server=[
        Choice(name="Nincord", value="mYjeaZQ"),
        Choice(name="Gary's homebrew stuff", value="geY4G2NZK9"),
        Choice(name="Puginator Productions", value="Yh2zWxugVE"),
        Choice(name="ResistanceYT's Hangout Lounge", value="ab6P4gB")])
    @app_commands.describe(server="The server to provide a link for.")
    async def invite(self, interaction: discord.Interaction, server: str):
        "Sends a link to an affiliated server."
        await interaction.response.send_message("Share this link to invite people! "
            + f"https://discord.gg/{server}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Inform(bot))
