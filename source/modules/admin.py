import discord

from discord import app_commands
from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    sudo_group = app_commands.Group(name="sudo",
        description="Commands for managing the bot.")

    def staff_check():
        def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.manage_messages
        return app_commands.check(predicate)


    @sudo_group.command()
    @app_commands.describe(
        recipient="The channel that will receive the message.",
        message="The message that you wish to send.")
    @staff_check()
    async def channel(self, interaction: discord.Interaction, recipient: discord.TextChannel,
        message: str):
        "Sends a message to a specified channel."
        await recipient.send(message) # Send the message
        # Sends a message to the channel that the command specifies.
        embed = discord.Embed(title=f"Sent to #{recipient}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)
        # Send the message to the channel that the command specifies.
        if interaction.channel != recipient:
            await interaction.response.send_message("Your message has been sent!",
                embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("Your message has been sent!",
                ephemeral=True)


    @sudo_group.command()
    @app_commands.describe(
        recipient="The member that will receive the message.",
        message="The message that you wish to send.")
    @staff_check()
    async def member(self, interaction: discord.Interaction, recipient: discord.Member,
        message: str):
        "Sends a message to a specified member."
        await recipient.send(message) # Send the message
        # Sends a direct message to the user that the command specifies.
        embed = discord.Embed(title=f"Sent to {recipient.name}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)
        # Send the message to the member that the command specifies.
        await interaction.response.send_message("Your message has been sent!",
            embed=embed, ephemeral=True)


    @sudo_group.command()
    @staff_check()
    async def reboot(self, interaction: discord.Interaction):
        "Reboots the bot by terminating its process."
        await interaction.response.send_message("The bot process will now be terminated.",
            ephemeral=True)
        await self.bot.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot), guilds=[discord.Object(id=450846070025748480)])
