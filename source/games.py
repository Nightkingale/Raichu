import aiohttp
import discord
import random

from discord import app_commands
from discord.ext import commands

from logger import create_logger

        
class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.logger = create_logger(self.__class__.__name__)


    # RiiTag no longer exists at this time.
    # Once it's replaced with LinkTag, we can update this code accordingly.

    # @app_commands.command()
    # @app_commands.describe(
    #     member="The member whose RiiTag should be searched for.")
    # async def riitag(self, interaction: discord.Interaction, member: discord.Member = None):
    #     "Shows a RiiTag from the RiiConnect24 service."
    #     if member == None:
    #         member = interaction.user
    #
    #     # Discord cache is wonky, so we need to add a randomizer to the URL.
    #     tag_link = f"https://tag.rc24.xyz/{member.id}/tag.max.png?randomizer={random.random()}"
    #
    #     # Check if the member has a RiiTag.
    #     await interaction.response.defer()
    #     async with self.session.get(tag_link) as response:
    #         # Check if the response from the site actually contains an image.
    #         if response.status == 200 and response.headers["content-type"] == "image/png":
    #             self.logger.info(f"A RiiTag was fetched for {member.display_name} at {tag_link}.")
    #             embed = discord.Embed(title=f"{member.display_name}'s RiiTag (via RiiConnect24)",
    #                 description="A showcase of recently played games on Nintendo consoles.",
    #                 url="https://tag.rc24.xyz/", color=0xffff00)
    #             # embed.set_author(name=member.name, icon_url=member.avatar)
    #             embed.set_footer(text="This feature is powered by an external service!")
    #             embed.set_image(url=tag_link)
    #             # Send the embed to the channel that the command was used in.
    #             await interaction.followup.send("A RiiTag was successfully found."
    #                 + " Here's what it looks like!", embed=embed)
    #         else:
    #             await interaction.followup.send("There is no associated RiiTag for this account!"
    #                 + " Visit <https://tag.rc24.xyz> for more information.")
                

    @app_commands.command()
    @app_commands.describe(
        user="The user whose trophy card should be searched for.")
    async def trophy(self, interaction: discord.Interaction, user: str):
        "Shows a trophy card from the PSNProfile service."
        # Check if the user has a PSNProfile.
        await interaction.response.defer()
        async with self.session.get(f"https://card.psnprofiles.com/1/{user}.png") as response:
            # Check if the response from the site actually contains a profile.
            if response.status == 200:
                self.logger.info(f"A PSNProfile was fetched for {user}.")
                embed = discord.Embed(title=f"{user}'s Trophy Card (via PSNProfiles)",
                    description="A showcase of trophies earned on PlayStation consoles.",
                    url=f"https://psnprofiles.com/{user}", color=0xffff00)
                embed.set_footer(text="This feature is powered by an external service!")
                embed.set_image(url=response.url)
                # Send the embed to the channel that the command was used in.
                await interaction.followup.send("A trophy card was successfully found."
                    + " Here's what it looks like!", embed=embed)
            else:
                await interaction.followup.send("There is no associated trophy card with this name!"
                    + " Visit <https://psnprofiles.com> for more information.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot))
