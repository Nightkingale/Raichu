import discord

from discord import app_commands
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    send_group = app_commands.Group(name="send",
        description="Commands for sending messages.")

    @send_group.command()
    @app_commands.describe(
        recipient="The channel that will receive the message.",
        message="The message that you wish to send.")
    async def channel(self, interaction: discord.Interaction, recipient: discord.TextChannel,
        message: str):
        "Sends a message to a specified channel."
        await recipient.send(message)

        embed = discord.Embed(title=f"Sent to #{recipient}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)

        if interaction.channel != recipient:
            await interaction.response.send_message("Your message has been sent!",
                embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Your message has been sent!",
                ephemeral=True)

    @send_group.command()
    @app_commands.describe(
        recipient="The member that will receive the message.",
        message="The message that you wish to send.")
    async def member(self, interaction: discord.Interaction, recipient: discord.Member,
        message: str):
        "Sends a message to a specified member."
        await recipient.send(message)

        embed = discord.Embed(title=f"Sent to {recipient.name}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)

        await interaction.response.send_message("Your message has been sent!",
            embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
