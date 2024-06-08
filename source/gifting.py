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


client = pymongo.MongoClient(secrets["MONGODB_URI_KEY"])
database = client["Gifting"]


class Gifting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)


    @app_commands.command()
    @app_commands.describe(
        giveaway="The name of the giveaway to join or leave.")
    async def toggle(self, interaction: discord.Interaction, giveaway: str):
        "Adds or removes yourself from a giveaway."
        # Check if the giveaway exists and is not archived.
        giveaway_entry = database["Ongoing"].find_one({"_id": giveaway})
        if not giveaway_entry:
            await interaction.response.send_message("That giveaway does not exist! Make sure you typed the name exactly as announced.",
                ephemeral=True)
            return
        # Initialize the users field if it doesn't exist.
        if "users" not in giveaway_entry:
            database["Ongoing"].update_one({"_id": giveaway}, {"$set": {"users": []}})
            giveaway_entry["users"] = []
        # Check if the user has already entered the giveaway.
        if interaction.user.id in giveaway_entry["users"]:
            database["Ongoing"].update_one({"_id": giveaway}, {"$pull": {"users": interaction.user.id}})
            await interaction.response.send_message(f"You have left the **{giveaway}** giveaway. We're sorry to see you go!", ephemeral=True)
            self.logger.info(f"{interaction.user.name} has left the {giveaway} giveaway.")
            return
        # Add the user to the giveaway.
        database["Ongoing"].update_one({"_id": giveaway}, {"$push": {"users": interaction.user.id}})
        await interaction.response.send_message(f"You have entered the **{giveaway}** giveaway! We wish you the best of luck!", ephemeral=True)
        self.logger.info(f"{interaction.user.name} has joined the {giveaway} giveaway.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Gifting(bot))
