import discord
import pymongo
import random

from discord import app_commands
from discord.ext import commands
from json import loads
from pathlib import Path

from logger import create_logger


secret = loads(Path("config/secret.json").read_text())


client = pymongo.MongoClient(secret["MONGODB_URI_KEY"])
database = client["Gifting"]


class Gifting(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)


    @app_commands.command()
    @app_commands.describe(
        giveaway="The name of the giveaway to join or leave.")
    async def gift(self, interaction: discord.Interaction, giveaway: str):
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


    @app_commands.command()
    @app_commands.describe(
        name="The name of the giveaway to manage.",
        amount="The amount of winners to choose.")
    @app_commands.default_permissions(manage_messages=True)
    async def give(self, interaction: discord.Interaction, name: str, amount: int = 0):
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Gifting(bot))
