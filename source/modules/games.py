import aiohttp
import discord
import random

from discord import app_commands
from discord.ext import commands
from json import loads
from pathlib import Path

shop_list = []
page_count = 0


class Fortnite(discord.ui.View):
    async def fortnite_item_shop(shop_list, page_count):
        embed = discord.Embed(title=f"Fortnite Cosmetic Shop ({page_count + 1}"
            + f" of {len(shop_list)} Items)", description="A catalog showcasing every"
            + " currently purchasable Fortnite cosmetic.", color=0xffff00)
        embed.add_field(name="Name", value=shop_list[page_count]["name"], inline=True)
        embed.add_field(name="Price", value=shop_list[page_count]["vBucks"], inline=True)
        embed.add_field(name="Category", value=shop_list[page_count]["storeCategory"], inline=True)
        embed.set_footer(text="This feature is powered by an external service!")
        embed.set_thumbnail(url=shop_list[page_count]["imageUrl"])
        return embed

    @discord.ui.button(label="Previous Item", emoji="\U00002B05")
    async def previous_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        global page_count
        global shop_list
        if page_count != 0:
            page_count -= 1
        else:
            page_count = len(shop_list) - 1

        embed = await Fortnite.fortnite_item_shop(shop_list, page_count)
        await interaction.response.edit_message(embed=embed)
        
    @discord.ui.button(label="Next Item", emoji="\U000027A1")
    async def next_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        global page_count
        global shop_list
        
        if page_count != len(shop_list) - 1:
            page_count += 1
        else:
            page_count = 0

        embed = await Fortnite.fortnite_item_shop(shop_list, page_count)
        await interaction.response.edit_message(embed=embed)


class Nintendo(discord.ui.View):
    def __init__(self):
        super().__init__()
        
        self.add_item(discord.ui.Button(label='Wii Guide', url="https://wii.guide/"))
        self.add_item(discord.ui.Button(label='Wii U Hacks Guide', url="https://wiiu.hacks.guide/"))

        
class Games(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    game_group = app_commands.Group(name="game",
        description="Commands for gaming services.")

    @game_group.command()
    async def fortnite(self, interaction: discord.Interaction):
        "Shows the current Fortnite: Battle Royale cosmetic shop."
        secrets = loads(Path("secrets.json").read_text())
        headers = {"TRN-Api-Key": secrets["TRACKER_KEY"]}
        shop_link = "https://api.fortnitetracker.com/v1/store"

        async with self.session.get(shop_link, headers=headers) as response:
            await interaction.response.defer()
            item_shop = await response.json()
            
            global shop_list
            global page_count
            shop_list = []
            page_count = 0

            for item in item_shop:
                shop_list.append(item)

        embed = await Fortnite.fortnite_item_shop(shop_list, page_count)
        await interaction.followup.send("Here's the current Fortnite cosmetic shop!",
            embed=embed, view=Fortnite())

    @game_group.command()
    @app_commands.describe(
        member="The member whose RiiTag should be searched for.")
    async def nintendo(self, interaction: discord.Interaction, member: discord.Member = None):
        "Shows your RiiTag through the RiiConnect24 service."
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
                    + " and how they can be used with a modified Wii or Wii U console.", 
                    ephemeral=True, view=Nintendo())


async def setup(bot: commands.Bot):
    await bot.add_cog(Games(bot), guilds=[discord.Object(id=450846070025748480)])
