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
database = client["Giveaways"]


class Gifting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)

    giveaway_group = app_commands.Group(name="giveaway",
        description="Commands for managing giveaways.")


    @giveaway_group.command()
    @app_commands.choices(giveaway=[
        app_commands.Choice(name="Heavenly Night (Digital Download)", value="Heavenly Night (Digital Download)")])
    @app_commands.describe(giveaway="The name of the giveaway to claim.")
    async def claim(self, interaction: discord.Interaction, giveaway: str):
        "Claims any gifts that you might be eligible for."
        if giveaway == "Heavenly Night (Digital Download)":
            # If the user does not have the eligible role, send an error message.
            if not discord.utils.get(interaction.user.roles, id=1192190765288411277):
                role = discord.utils.get(interaction.guild.roles, id=1192190765288411277)
                await interaction.response.send_message(f"You are not a {role.name}, so you are not eligible to claim this gift.",
                    ephemeral=True)
                return
            hn_giveaway = database["Certificate"].find_one({"_id": "Heavenly Night"})
            ttt_giveaway = database["Certificate"].find_one({"_id": "To the Throwbacks"})
            # If the user has already claimed the gift, send an error message.
            if interaction.user.id in hn_giveaway["users"] or interaction.user.id in ttt_giveaway["users"]:
                await interaction.response.send_message("You have already claimed this gift!",
                    ephemeral=True)
                return
            # Randomly pick one code from each to give to the user.
            hn_code = random.choice(hn_giveaway["codes"])
            ttt_code = random.choice(ttt_giveaway["codes"])
            # Make an embed for the gift codes.
            embed = discord.Embed(title=giveaway,
                description="Redeem: https://redeem.nightkingale.com/",
                color=0xffff00)
            embed.set_thumbnail(url="https://f4.bcbits.com/img/0034764402_10.jpg")
            embed.add_field(name="Heavenly Night", value=hn_code)
            embed.add_field(name="To the Throwbacks", value=ttt_code)
            embed.set_footer(text="Please contact a member of the Nincord staff team if you have any issues.")
            await interaction.response.send_message("You have successfully claimed your gift! Please check your direct messages for your gift codes.",
                ephemeral=True)
            # Attempt to send a message to the user. If it doesn't work, let the user know and stop.
            try:
                await interaction.user.send("Thank you so much for supporting Nightkingale! Please see below for your gift.",
                    embed=embed)
            except discord.Forbidden:
                await interaction.followup.send("Your gift could not be sent to you! Please make sure you have direct messages enabled and try again.",
                    ephemeral=True)
                return
            self.logger.info(f"{interaction.user.name} has claimed their {giveaway} gift.")
            # Add the user to the giveaway.
            database["Certificate"].update_one({"_id": "Heavenly Night"}, {"$push": {"users": interaction.user.id}})
            database["Certificate"].update_one({"_id": "To the Throwbacks"}, {"$push": {"users": interaction.user.id}})
            # Remove the code from the giveaway.
            database["Certificate"].update_one({"_id": "Heavenly Night"}, {"$pull": {"codes": hn_code}})
            database["Certificate"].update_one({"_id": "To the Throwbacks"}, {"$pull": {"codes": ttt_code}})


    @giveaway_group.command()
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
    await bot.add_cog(Gifting(bot), guilds=[discord.Object(id=450846070025748480)])
