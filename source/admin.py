import discord
import os
import pymongo
import random

from discord import app_commands
from discord.ext import commands
from json import loads
from logger import create_logger
from pathlib import Path


try:
    # Attempt to load the secrets from a file.
    secrets = loads(Path("secrets.json").read_text())
except FileNotFoundError:
    # This is used as a fallback when the secrets file doesn't exist.
    secrets = {"MONGODB_URI_KEY": os.environ["MONGODB_URI_KEY"]}


client = pymongo.MongoClient(secrets["MONGODB_URI_KEY"])
database = client["Gifting"]


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
    @app_commands.describe(
        name="The name of the giveaway to manage.",
        amount="The amount of winners to choose.")
    @app_commands.default_permissions(manage_messages=True)
    async def giveaway(self, interaction: discord.Interaction, name: str, amount: int = 0):
        "Starts a giveaway, or ends it if amount is specified."
        if amount < 1:
            # Check if the giveaway already exists.
            if database["Ongoing"].find_one({"_id": name}):
                await interaction.response.send_message("That giveaway already exists! Please choose a different name.",
                    ephemeral=True)
                return
            # Create a new giveaway.
            database["Ongoing"].insert_one({"_id": name, "host": interaction.user.id, "users": []})
            await interaction.response.send_message(f"The **{name}** giveaway has been started! "
                + "Please use the `end` action to choose a winner.",
                ephemeral=True)
            self.logger.info(f"{interaction.user.name} has started the {name} giveaway.")
        else:
            # Check if the giveaway exists.
            giveaway_entry = database["Ongoing"].find_one({"_id": name})
            if not giveaway_entry:
                await interaction.response.send_message("That giveaway does not exist! Make sure you typed the name exactly as announced.",
                    ephemeral=True)
                return
            # Check if the amount of winners is valid.
            if amount < 1:
                await interaction.response.send_message("You must choose at least one winner for the giveaway!",
                    ephemeral=True)
                return
            if amount > len(giveaway_entry["users"]):
                participant_count = len(giveaway_entry["users"])
                await interaction.response.send_message(
                    f"You cannot choose more winners than there are participants (currently {participant_count}).",
                    ephemeral=True
                )
                return
            # Choose winner(s), making sure not to pick the same person twice.
            winners = random.sample(giveaway_entry["users"], amount)
            # Send a message to the channel congratulating and mentioning the winner(s).
            winner_ids = [f'<@{winner_id}>' for winner_id in winners]
            # Create an embed for the giveaway winner(s).
            embed = discord.Embed(title=f"Winner{'s' if amount > 1 else ''} of the {name} Giveaway",
                description=f"Congratulations to the winner{'s' if amount > 1 else ''} of the giveaway!", color=0xffff00)
            try:
                host = await self.bot.fetch_user(giveaway_entry["host"])
            except discord.NotFound:
                host = interaction.user
            embed.set_author(name=host.display_name, icon_url=host.display_avatar)
            embed.set_thumbnail(url="https://media.tenor.com/3fBEgjA2Y6IAAAAi/giveaway-alert-giveaway.gif")
            embed.add_field(name=f"Winner{'s' if amount > 1 else ''} ({amount} total)", value="\n".join(winner_ids))
            embed.set_footer(text="A notification will be sent. Please contact the host to claim your gift.")
            # Attempt to send a message to the chosen winners.
            for winner in winner_ids:
                winner = await self.bot.fetch_user(winner[2:-1])
                if winner:
                    await winner.send(
                        f"Congratulations! You have won the **{name}** giveaway on the {interaction.guild.name} server!\n\n"
                        f"Please contact the host ({host.mention}) or a member of the {interaction.guild.name} staff team "
                        f"in order to proceed and claim your prize. If the host or a staff member has already reached out to you, "
                        f"please disregard this message. Thank you so much for your participation!",
                        embed=embed
                    )
                    self.logger.info(f"Sent a message to {winner.name} regarding a giveaway.")
            # Send a message to the channel that the giveaway has ended.
            await interaction.response.send_message(f"The results are in for the **{name}** giveaway! Congratulations!",
                embed=embed)
            self.logger.info(f"{interaction.user.name} has decided for the {name} giveaway.")
            # Move the giveaway to Archived from Ongoing.
            database["Archived"].replace_one({"_id": name}, giveaway_entry, upsert=True)
            database["Ongoing"].delete_one({"_id": name})


    @sudo_group.command()
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
        self.logger.info(f"{ctx.author.name} has requested a command sync.")
        await self.bot.tree.sync()
        await ctx.send("The sync has been completed successfully.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
