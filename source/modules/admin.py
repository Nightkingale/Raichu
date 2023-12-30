import discord
import os
import pymongo

from discord import app_commands
from discord.ext import commands
from json import loads
from modules.logger import create_logger
from pathlib import Path


try:
    # Attempt to load the secrets from a file.
    secrets = loads(Path("secrets.json").read_text())
except FileNotFoundError:
    # This is used as a fallback when the secrets file doesn't exist.
    secrets = {"MONGODB_URI_KEY": os.environ["MONGODB_URI_KEY"]}


client = pymongo.MongoClient(secrets["MONGODB_URI_KEY"])
database = client["Giveaways"]


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)

    send_group = app_commands.Group(name="send",
        description="Commands for sending messages as the bot.")
    sudo_group = app_commands.Group(name="sudo",
        description="Commands for managing the bot and databases.")
    

    @send_group.command()
    @app_commands.describe(
        recipient="The channel that will receive the message.",
        message="The message that you wish to send.")
    @app_commands.default_permissions(manage_messages=True)
    async def channel(self, interaction: discord.Interaction, recipient: discord.TextChannel,
        message: str):
        "Sends a message to a specified channel."
        await recipient.send(message) # Send the message
        # Sends a message to the channel that the command specifies.
        embed = discord.Embed(title=f"Sent to #{recipient}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)
        # Send the message to the channel that the command specifies.
        if interaction.channel != recipient:
            await interaction.response.send_message("Your message has been sent!",
                embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Your message has been sent!",
                ephemeral=True)
        self.logger.info(f"{interaction.user.name} sent a message to #{recipient}.")


    @send_group.command()
    @app_commands.describe(
        recipient="The member that will receive the message.",
        message="The message that you wish to send.")
    @app_commands.default_permissions(manage_messages=True)
    async def member(self, interaction: discord.Interaction, recipient: discord.Member,
        message: str):
        "Sends a message to a specified member."
        await recipient.send(message) # Send the message
        # Sends a direct message to the user that the command specifies.
        embed = discord.Embed(title=f"Sent to {recipient.name}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)
        # Send the message to the member that the command specifies.
        await interaction.response.send_message("Your message has been sent!",
            embed=embed, ephemeral=True)
        self.logger.info(f"{interaction.user.name} sent a message to {recipient.name}.")


    @sudo_group.command()
    @app_commands.default_permissions(manage_messages=True)
    async def giveaway(self, interaction: discord.Interaction, giveaway: str):
        "Start a new giveaway."
        # Check if the giveaway already exists.
        if database["Ongoing"].find_one({"_id": giveaway}):
            await interaction.response.send_message("That giveaway already exists! Please choose a different name.",
                ephemeral=True)
            return
        # Create a new giveaway.
        database["Ongoing"].insert_one({"_id": giveaway, "host": interaction.user.id, "users": []})
        await interaction.response.send_message(f"The **{giveaway}** giveaway has been started! "
            + "Please use the `/giveaway decide` command to choose a winner.",
            ephemeral=True)
        self.logger.info(f"{interaction.user.name} has started the {giveaway} giveaway.")


    @sudo_group.command()
    @app_commands.default_permissions(manage_messages=True)
    async def reboot(self, interaction: discord.Interaction):
        "Reboots the bot by terminating its process."
        await interaction.response.send_message("The bot process will now be terminated.",
            ephemeral=True)
        self.logger.info(f"{interaction.user.name} has requested a reboot of the bot.")
        await self.bot.close()


    @sudo_group.command()
    @app_commands.default_permissions(manage_messages=True)
    async def status(self, interaction: discord.Interaction, text: str = None):
        "Change the status to the specified text, or reset it back to default."
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot), guilds=[discord.Object(id=450846070025748480)])
