import discord
import os
import pymongo

from discord import app_commands
from discord.ext import commands
from json import loads
from pathlib import Path

from logger import create_logger


try:
    # Attempt to load the secrets from a file.
    secrets = loads(Path("secrets.json").read_text())
except FileNotFoundError:
    # This is used as a fallback when the secrets file doesn't exist.
    secrets = {"MONGODB_URI_KEY": os.environ["MONGODB_URI_KEY"]}


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)


    @app_commands.command()
    @app_commands.describe(
        recipient="The channel or member that will receive the message.",
        message="The message that you wish to send.")
    @app_commands.default_permissions(manage_messages=True)
    async def send(self, interaction: discord.Interaction, recipient: str, message: str):
        "Sends a message to a specified channel or member."
        # Try to resolve the recipient as a Member or Channel.
        recipient_id = int(recipient.strip('<@!#>'))
        recipient_object = interaction.guild.get_member(recipient_id) or interaction.guild.get_channel(recipient_id)
        if recipient_object is None:
            await interaction.response.send_message("The recipient provided was invalid!", ephemeral=True)
            return
        await recipient_object.send(message)
        # Prepares a success message with a preview of the sent message.
        recipient_name = recipient_object.name if isinstance(recipient_object, discord.Member) else f"#{recipient_object.name}"
        embed = discord.Embed(title=f"Sent to {recipient_name}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)
        await interaction.response.send_message("Your message has been sent!",
            embed=embed, ephemeral=True)
        self.logger.info(f"{interaction.user.name} sent a message to {recipient_name}.")


    @app_commands.command()
    @app_commands.default_permissions(manage_messages=True)
    async def status(self, interaction: discord.Interaction, text: str = None):
        "Resets the status, or changes it if text is specified."
        if text is None:
            activity = discord.Activity(
                name="Nincord", type=discord.ActivityType.watching)
            await self.bot.change_presence(activity=activity)
            await interaction.response.send_message("The status has been reset successfully.",
                ephemeral=True)
        else:
            await self.bot.change_presence(activity=discord.Game(name=text))
            await interaction.response.send_message("The status has been changed successfully.",
                ephemeral=True)
        self.logger.info(f"{interaction.user.name} has changed the bot's status.")


    @commands.command(hidden=True)
    @commands.is_owner()
    async def reboot(self, ctx):
        "Reboots the bot by terminating its process and prompting Heroku."
        await ctx.send("The bot process will now be terminated.")
        self.logger.info(f"{ctx.author.name} has requested a reboot of the bot.")
        await self.bot.close()


    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx):
        "Syncs the bot's commands with Discord."
        await self.bot.tree.sync()
        self.logger.info(f"{ctx.author.name} has requested a command sync.")
        await ctx.send("The sync has been completed successfully.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
