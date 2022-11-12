import aiohttp
import discord
import random

from discord import app_commands
from discord.ext import commands


class Nintendo(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(discord.ui.Button(
            label='Wii Guide', url="https://wii.guide/"))
        self.add_item(discord.ui.Button(
            label='Wii U Hacks Guide', url="https://wiiu.hacks.guide/"))

        
class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    games_group = app_commands.Group(name="games",
        description="Commands for gaming services.")

    @games_group.command()
    @app_commands.describe(
        member="The member whose RiiTag should be searched for.")
    async def riitag(self, interaction: discord.Interaction, member: discord.Member = None):
        "Shows a RiiTag from the RiiConnect24 service."
        if member == None:
            member = interaction.user

        tag_link = f"https://tag.rc24.xyz/{member.id}/tag.max.png?randomizer={random.random()}"
        
        async with self.session.get(tag_link) as response:
            if response.headers["content-type"] == "image/png":
                await interaction.response.defer()
                embed = discord.Embed(title=f"{member.display_name}'s RiiTag (via RiiConnect24)",
                    description="A showcase of recently played games on Nintendo Wii and Wii U.",
                    url="https://tag.rc24.xyz/", color=0xffff00)
                embed.set_author(name=member.name, icon_url=member.avatar)
                embed.set_footer(text="This feature is powered by an external service!")
                embed.set_image(url=tag_link)

                await interaction.followup.send("A RiiTag has been found! "
                    + "Here's what it looks like.", embed=embed)
            else:
                await interaction.response.send_message("There is no associated RiiTag for this account!"
                    + " To set one up, visit <https://tag.rc24.xyz/> for more information about RiiTags"
                    + " and how they can be used with a modified Wii or Wii U console.", view=Nintendo())

async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot), guilds=[discord.Object(id=450846070025748480)])
