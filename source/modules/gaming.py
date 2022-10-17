import discord
import random
import requests

from discord import app_commands
from discord.ext import commands


class Gaming(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    service_group = app_commands.Group(name="service",
        description="Commands for gaming services.")

    @service_group.command()
    @app_commands.describe(
        member="The member whose RiiTag should be searched for.")
    async def riitag(self, interaction: discord.Interaction, member: discord.Member = None):
        "Show your RiiTag through the RiiConnect24 service."
        if member == None:
            member = interaction.user

        tag_link = f"https://tag.rc24.xyz/{member.id}/tag.max.png?randomizer={random.random()}"
        request = requests.head(tag_link)

        if request.headers["content-type"] == "image/png":
            embed = discord.Embed(title=f"{member.display_name}'s RiiTag", color=0xffff00)
            embed.set_author(name=member.name, icon_url=member.avatar)
            embed.set_footer(text="This feature is powered by the RiiConnect24 service!")
            embed.set_image(url=tag_link)

            await interaction.response.send_message("The corresponding RiiTag has been found! "
                + "Here's what it looks like.", embed=embed)
        else:
            await interaction.response.send_message("There is no associated RiiTag for this account!"
                + " To set one up, visit <https://tag.rc24.xyz/> for more information about RiiTags"
                + " and how they can be used with a modified Wii or Wii U console.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Gaming(bot), guilds=[discord.Object(id=450846070025748480)])
