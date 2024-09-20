from redbot.core import commands, Config
import discord
import asyncio

class StatusRotator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        self.status_task = self.bot.loop.create_task(self.change_status())
        self.statuses = [
            ("watching", lambda: f"Serving {len(self.bot.guilds)} servers"),
            ("watching", lambda: f"Serving {len(self.bot.users)} users"),
            ("playing", lambda: f"Uptime: {self.get_uptime()}"),
        ]
        if self.bot.get_cog("AntiPhishing"):
            self.statuses.append(("watching", lambda: f"for {self.get_blocked_domains_count()} bad domains"))

    def cog_unload(self):
        self.status_task.cancel()

    async def change_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            for activity_type, status in self.statuses:
                if activity_type == "watching":
                    activity = discord.Activity(type=discord.ActivityType.watching, name=status())
                elif activity_type == "listening":
                    activity = discord.Activity(type=discord.ActivityType.listening, name=status())
                elif activity_type == "playing":
                    activity = discord.Game(name=status())
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(60)  # Change status every 60 seconds

    def get_uptime(self):
        delta = discord.utils.utcnow() - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

    def get_blocked_domains_count(self):
        antiphishing_cog = self.bot.get_cog("AntiPhishing")
        if antiphishing_cog:
            return len(antiphishing_cog.blocked_domains)
        return 0

    @commands.Cog.listener()
    async def on_ready(self):
        if not hasattr(self.bot, 'uptime'):
            self.bot.uptime = discord.utils.utcnow()
