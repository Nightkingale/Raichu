import discord
import os

from discord import app_commands
from discord.ext import commands


class Moderate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.describe(
        channel="The channel that will receive the message.",
        message="The message that you wish to send.")
    async def talk(self, interaction: discord.Interaction, channel: discord.TextChannel,
        message: str):
        "Sends a message to a specified channel."
        await channel.send(message)

        embed = discord.Embed(title=f"Sent to #{channel}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)

        if interaction.channel != channel:
            await interaction.response.send_message("Your message has been sent!",
                embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Your message has been sent!",
                ephemeral=True)

    @app_commands.command()
    @app_commands.describe(
        member="The member that will receive the message.",
        message="The message that you wish to send.")
    async def send(self, interaction: discord.Interaction, member: discord.Member,
        message: str):
        "Sends a message to a specified member."
        await member.send(message)

        embed = discord.Embed(title=f"Sent to {member.name}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)

        await interaction.response.send_message("Your message has been sent!",
            embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderate(bot), guilds=[discord.Object(id=450846070025748480)])
