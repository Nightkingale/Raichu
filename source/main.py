import discord
import os

from discord.ext import commands
from json import loads
from pathlib import Path

from logger import create_logger


class Manager(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            help_command=None,
            intents=discord.Intents.all(),
            application=983846918683770941,
            # The server name here is staying as is. Old server reference!
            activity=discord.Activity(name="Nincord", type=discord.ActivityType.watching),
            status=discord.Status.online
        )
        self.logger = create_logger("Main")


    async def setup_hook(self):
        for filename in os.listdir("./source"):
            # Load all of the modules in the modules folder.
            if filename.endswith(".py") and filename not in ["main.py", "logger.py"]:
                await self.load_extension(f"{filename[:-3]}")
                self.logger.info(f"Loaded {filename} successfully from the modules folder.")


    @commands.command(hidden=True)
    @commands.is_owner()
    async def cog(self, ctx, action, cog):
        "Load, unload, or reload a cog."
        if action not in ["load", "unload", "reload"]:
            await ctx.send("Invalid action. Please use 'load', 'unload', or 'reload'.")
            return
        if cog in ["main", "logger"]:
            await ctx.send("You cannot perform this action on the main or logger cog.")
            return
        if action == "load":
            self.load_extension(f"source.{cog}")
            await ctx.send(f"{cog} was loaded successfully.")
        elif action == "unload":
            self.unload_extension(f"source.{cog}")
            await ctx.send(f"{cog} was unloaded successfully.")
        elif action == "reload":
            self.reload_extension(f"source.{cog}")
            await ctx.send(f"{cog} was reloaded successfully.")


    @commands.command(hidden=True)
    @commands.is_owner()
    async def reboot(self, ctx):
        "Reboots the bot by terminating its process and prompting Heroku."
        await ctx.send("The bot process will now be terminated.")
        self.logger.info(f"{ctx.author.name} has requested a reboot of the bot.")
        await self.bot.close()


    @commands.command(hidden=True)
    @commands.is_owner()
    async def sync(self, ctx):
        "Syncs the bot's commands with Discord."
        await self.bot.tree.sync()
        self.logger.info(f"{ctx.author.name} has requested a command sync.")
        await ctx.send("The sync has been completed successfully.")


try:
    # Attempt to load the secrets from a file.
    secrets = loads(Path("secrets.json").read_text())
except FileNotFoundError:
    # This is used as a fallback when the secrets file doesn't exist.
    secrets = {"DISCORD_BOT_TOKEN": os.environ["DISCORD_BOT_TOKEN"]}


bot = Manager() # Run the bot.
bot.run(secrets["DISCORD_BOT_TOKEN"], log_handler=None)
