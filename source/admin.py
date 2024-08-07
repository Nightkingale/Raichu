import discord
import os

from discord import app_commands
from discord.ext import commands

from logger import create_logger


class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = create_logger(self.__class__.__name__)


    @app_commands.command()
    @app_commands.describe(
        recipient="The channel or member that will receive the message.",
        message="The message that you wish to send.")
    @app_commands.default_permissions(manage_messages=True)
    async def send(self, interaction: discord.Interaction, recipient: str, message: str):
        "Sends a message to a specified channel or member."
        # Try to resolve the recipient as a Member or Channel.
        recipient_id = int(recipient.strip('<@!#>'))
        recipient_object = interaction.guild.get_member(recipient_id) or interaction.guild.get_channel(recipient_id)
        if recipient_object is None:
            await interaction.response.send_message("The recipient provided was invalid!", ephemeral=True)
            return
        allowed_mentions = discord.AllowedMentions(everyone=False, roles=True, users=True)

        # Check if the sender could mention everyone, then set the allowed mentions accordingly.
        if interaction.channel.permissions_for(interaction.user).mention_everyone:
            allowed_mentions.everyone = True
        await recipient_object.send(message, allowed_mentions=allowed_mentions)

        # Prepares a success message with a preview of the sent message.
        recipient_name = recipient_object.name if isinstance(recipient_object, discord.Member) else f"#{recipient_object.name}"
        embed = discord.Embed(title=f"Sent to {recipient_name}",
            description="A preview of your sent message.", color=0xffff00)
        embed.set_author(name=interaction.user.name,
            icon_url=interaction.user.avatar)
        embed.add_field(name="Message", value=message)
        await interaction.response.send_message("Your message has been sent!",
            embed=embed, ephemeral=True)
        self.logger.info(f"{interaction.user.name} sent a message to {recipient_name}.")


    @app_commands.command()
    @app_commands.default_permissions(manage_messages=True)
    async def status(self, interaction: discord.Interaction, text: str = None):
        "Resets the status, or changes it if text is specified."
        if text is None:
            activity = discord.Activity(
                name="Nincord", type=discord.ActivityType.watching)
            await self.bot.change_presence(activity=activity)
            await interaction.response.send_message("The status has been reset successfully.",
                ephemeral=True)
        else:
            await self.bot.change_presence(activity=discord.Game(name=text))
            await interaction.response.send_message("The status has been changed successfully.",
                ephemeral=True)
        self.logger.info(f"{interaction.user.name} has changed the bot's status.")


    @commands.command(hidden=True)
    @commands.is_owner()
    async def cog(self, ctx, action, cog):
        "Load, unload, or reload a cog."
        cog = cog.lower()
        if action not in ["load", "unload", "reload"]:
            await ctx.reply("This action is not valid! Please use 'load', 'unload', or 'reload'.")
            return
        
        if cog in ["main", "admin", "logger"]:
            await ctx.reply("You cannot perform this action on the main, logger, or admin cogs.")
            return
        
        try:
            self.logger.info(f"{ctx.author.name} has requested to {action} the {cog} cog.")
            if action == "load":
                await self.bot.load_extension(f"{cog}")
                await ctx.reply(f"The {cog} cog was loaded successfully.")
            elif action == "unload":
                await self.bot.unload_extension(f"{cog}")
                await ctx.reply(f"The {cog} cog was unloaded successfully.")
            elif action == "reload":
                await self.bot.reload_extension(f"{cog}")
                await ctx.reply(f"The {cog} cog was reloaded successfully.")
            await self.bot.tree.sync() # Attempt to sync the commands automatically.
        except Exception as error:
            await ctx.reply(f"An exception has occurred! Please check the logs for more information.")
            self.logger.error(f"An exception has been caught!", exc_info=error)


    @commands.command(hidden=True)
    @commands.is_owner()
    async def reboot(self, ctx, update: bool = True):
        "Reboots the bot and checks for updates."
        if update:
            await ctx.reply("The bot will now terminate and update.")
            self.logger.info(f"{ctx.author.name} has requested an update of the bot.")
            if os.name == "posix":
                # Run the updater service in Area Zero.
                os.system("sudo systemctl start raichu_update.service")
            else:
                await self.bot.close()
        else:
            await ctx.reply("The bot will now terminate and restart.")
            self.logger.info(f"{ctx.author.name} has requested a reboot of the bot.")
            if os.name == "posix":
                # Restart Raichu's service in Area Zero.
                os.system("sudo systemctl restart raichu.service")
            else:
                await self.bot.close()


    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx):
        "Syncs the bot's commands with Discord."
        await self.bot.tree.sync()
        self.logger.info(f"{ctx.author.name} has requested a command sync.")
        await ctx.reply("The sync has been completed successfully.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
