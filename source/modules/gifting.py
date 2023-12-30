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


class Gifting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)

    giveaway_group = app_commands.Group(name="giveaway",
        description="Commands for managing giveaways.")

    def staff_check():
        def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.manage_messages
        return app_commands.check(predicate)


    @giveaway_group.command()
    @app_commands.describe(
        giveaway="The name of the giveaway to join or leave.")
    async def toggle(self, interaction: discord.Interaction, giveaway: str):
        "Add or remove yourself from a giveaway."
        # Check if the giveaway exists and is not archived.
        if not database.list_collection_names().__contains__(giveaway) or database[giveaway].name.endswith("[archive]"):
            await interaction.response.send_message("That giveaway does not exist! Make sure you typed the name exactly as announced.",
                ephemeral=True)
            return
        # Check if the user has already entered the giveaway.
        if database[giveaway].find_one({"_id": interaction.user.id}):
            database[giveaway].delete_one({"_id": interaction.user.id})
            await interaction.response.send_message(f"You have left the **{giveaway}** giveaway. We're sorry to see you go!", ephemeral=True)
            self.logger.info(f"{interaction.user.name} has left the giveaway.")
            return
        # Add the user to the giveaway.
        database[giveaway].insert_one({"_id": interaction.user.id})
        await interaction.response.send_message(f"You have entered the **{giveaway}** giveaway! We wish you the best of luck!", ephemeral=True)
        self.logger.info(f"{interaction.user.name} has joined the giveaway.")


    @giveaway_group.command()
    @staff_check()
    async def decide(self, interaction: discord.Interaction, giveaway: str, amount: int):
        "Decide a winner for a specified giveaway."
        # Check if the giveaway exists.
        if not database.list_collection_names().__contains__(giveaway) or database[giveaway].name.endswith("[archive]"):
            await interaction.response.send_message("That giveaway does not exist! Make sure you typed the name exactly as announced.",
                ephemeral=True)
            return
        # Check if the amount of winners is valid.
        if amount < 1:
            await interaction.response.send_message("You must choose at least one winner for the giveaway!",
                ephemeral=True)
            return
        if amount > database[giveaway].estimated_document_count():
            participant_count = database[giveaway].estimated_document_count()
            await interaction.response.send_message(
                f"You cannot choose more winners than there are participants (currently {participant_count}).",
                ephemeral=True
            )
            return
        # Choose winner(s), making sure not to pick the same person twice.
        winner = database[giveaway].aggregate([{"$sample": {"size": amount}}])
        # Send a message to the channel congratulating and mentioning the winner(s).
        winner_ids = [f'<@{document["_id"]}>' for document in winner]
        # Create an embed for the giveaway winner(s).
        embed = discord.Embed(title=f"Winner{'s' if amount > 1 else ''} of the {giveaway} Giveaway",
            description=f"Congratulations to the winner{'s' if amount > 1 else ''} of the giveaway!", color=0xffff00)
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
        embed.set_thumbnail(url="https://media.tenor.com/3fBEgjA2Y6IAAAAi/giveaway-alert-giveaway.gif")
        embed.add_field(name=f"Winner{'s' if amount > 1 else ''} ({amount} total)", value="\n".join(winner_ids))
        embed.set_footer(text="A notification will be sent. Please contact the host to claim your gift.")
        # Attempt to send a message to the chosen winners.
        for winner in winner_ids:
            winner = await self.bot.fetch_user(winner[2:-1])
            if winner:
                await winner.send(
                    f"Congratulations! You have won the **{giveaway}** giveaway on the {interaction.guild.name} server!\n\n"
                    f"Please contact the host ({interaction.user.mention}) or a member of the {interaction.guild.name} staff team "
                    f"in order to proceed and claim your prize. If the host or a staff member has already reached out to you, "
                    f"please disregard this message. Thank you so much for your participation!",
                    embed=embed
                )
                self.logger.info(f"Sent a message to {winner.name} regarding a giveaway.")
        # Send a message to the channel that the giveaway has ended.
        await interaction.response.send_message(f"The results are in for the **{giveaway}** giveaway! Congratulations!",
            embed=embed)
        self.logger.info(f"{interaction.user.name} has decided for the {giveaway} giveaway.")
        # Close the giveaway.
        database[giveaway].rename(f"{giveaway} [archive]")


async def setup(bot: commands.Bot):
    await bot.add_cog(Gifting(bot), guilds=[discord.Object(id=450846070025748480)])
