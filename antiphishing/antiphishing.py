import contextlib
import datetime
import re
from typing import List
from urllib.parse import urlparse
import aiohttp # type: ignore
import discord # type: ignore
from discord.ext import tasks # type: ignore
from redbot.core import Config, commands, modlog # type: ignore
from redbot.core.bot import Red # type: ignore
from redbot.core.commands import Context # type: ignore

URL_REGEX_PATTERN = re.compile(
    r"^(?:http[s]?:\/\/)?[\w]+(?:\.[\w]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"
)


class AntiPhishing(commands.Cog):
    """
    Guard users from malicious links and phishing attempts with customizable protection options.
    """

    __version__ = "1.1.2"
    __last_updated__ = "Jul 5 2024"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=73835)
        self.config.register_guild(action="notify", caught=0, notifications=0, deletions=0, kicks=0, bans=0, max_links=3, last_updated=None)
        self.config.register_member(caught=0)
        self.session = aiohttp.ClientSession()
        self.bot.loop.create_task(self.register_casetypes())
        self.bot.loop.create_task(self.get_phishing_domains())
        self.domains = []

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs):
        return

    def format_help_for_context(self, ctx: Context) -> str:
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nVersion {self.__version__}"

    async def register_casetypes(self) -> None:
        with contextlib.suppress(RuntimeError):
            await modlog.register_casetype(
                name="phish_found",
                default_setting=True,
                image="🎣",
                case_str="Malicious link detected",
            )
            # delete setting
            await modlog.register_casetype(
                name="phish_deleted",
                default_setting=True,
                image="🎣",
                case_str="Malicious link actioned",
            )
            # kick setting
            await modlog.register_casetype(
                name="phish_kicked",
                default_setting=True,
                image="🎣",
                case_str="Malicious link actioned",
            )
            # ban setting
            await modlog.register_casetype(
                name="phish_banned",
                default_setting=True,
                image="🎣",
                case_str="Malicious link actioned",
            )

    @tasks.loop(minutes=10)
    async def get_phishing_domains(self) -> None:
        domains = []

        headers = {
            "X-Identity": f"BeeHive AntiPhishing v{self.__version__} (https://www.beehive.systems/sentri)",
        }

        async with self.session.get(
            "https://phish.sinking.yachts/v2/all", headers=headers
        ) as request:
            if request.status == 200:
                data = await request.json()
                domains.extend(data)

        async with self.session.get(
            "https://www.beehive.systems/hubfs/blocklist/blocklist.json", headers=headers
        ) as request:
            if request.status == 200:
                try:
                    data = await request.json()
                    if isinstance(data, list):
                        domains.extend(data)
                    else:
                        # Log or handle unexpected data format
                        print("Unexpected data format received from blocklist.")
                except Exception as e:
                    # Log or handle JSON parsing error
                    print(f"Error parsing JSON from blocklist: {e}")
            else:
                # Log or handle non-200 status code
                print(f"Failed to fetch blocklist, status code: {request.status}")
        deduped = list(set(domains))
        self.domains = deduped

    def extract_urls(self, message: str) -> List[str]:
        """
        Extract URLs from a message.
        """
        # Find all regex matches
        matches = URL_REGEX_PATTERN.findall(message)
        return matches

    def get_links(self, message: str) -> List[str]:
        """
        Get links from the message content.
        """
        # Remove zero-width spaces
        message = message.replace("\u200b", "")
        message = message.replace("\u200c", "")
        message = message.replace("\u200d", "")
        message = message.replace("\u2060", "")
        message = message.replace("\uFEFF", "")
        if message != "":
            links = self.extract_urls(message)
            if not links:
                return
            return list(set(links))

    async def handle_phishing(self, message: discord.Message, domain: str) -> None:
        domain = domain[:250]
        action = await self.config.guild(message.guild).action()
        if not action == "ignore":
            count = await self.config.guild(message.guild).caught()
            await self.config.guild(message.guild).caught.set(count + 1)
        member_count = await self.config.member(message.author).caught()
        max_links = await self.config.guild(message.guild).max_links()
        if member_count + 1 >= max_links:
            action = "ban"
        await self.config.member(message.author).caught.set(member_count + 1)
        if action == "notify":
            if message.channel.permissions_for(message.guild.me).send_messages:
                with contextlib.suppress(discord.NotFound):
                    mod_roles = await self.bot.get_mod_roles(message.guild)
                    mod_mentions = " ".join(role.mention for role in mod_roles) if mod_roles else ""
                    embed = discord.Embed(
                        title="Dangerous link detected!",
                        description=f"This message contains a malicious website or URL.\n\nThis URL could be anything from a fraudulent online seller, to an IP logger, to a page delivering malware intended to steal Discord accounts.\n\n**Don't click any links in this message, and notify server moderators ASAP**",
                        color=16729413,
                    )
                    embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/warning.png")
                    embed.timestamp = datetime.datetime.utcnow()
                    embed.set_footer(text="Link scanning powered by BeeHive",icon_url="")
                    if mod_mentions:
                        await message.channel.send(content=mod_mentions, allowed_mentions=discord.AllowedMentions(roles=True))
                    await message.reply(embed=embed)
                    
                await modlog.create_case(
                    guild=message.guild,
                    bot=self.bot,
                    created_at=datetime.datetime.utcnow(),
                    action_type="phish_found",
                    user=message.author,
                    moderator=message.guild.me,
                    reason=f"Sent a malicious URL **`{domain}`** in the server",
                )
                notifications = await self.config.guild(message.guild).notifications()
                await self.config.guild(message.guild).notifications.set(notifications + 1)
        elif action == "delete":
            if message.channel.permissions_for(message.guild.me).manage_messages:
                with contextlib.suppress(discord.NotFound):
                    await message.delete()

                await modlog.create_case(
                    guild=message.guild,
                    bot=self.bot,
                    created_at=datetime.datetime.utcnow(),
                    action_type="phish_deleted",
                    user=message.author,
                    moderator=message.guild.me,
                    reason=f"Sent a malicious URL **`{domain}`** in the server",
                )
                deletions = await self.config.guild(message.guild).deletions()
                await self.config.guild(message.guild).deletions.set(deletions + 1)
        elif action == "kick":
            if (
                message.channel.permissions_for(message.guild.me).kick_members
                and message.channel.permissions_for(message.guild.me).manage_messages
            ):
                with contextlib.suppress(discord.NotFound):
                    await message.delete()
                    if (
                        message.author.top_role >= message.guild.me.top_role
                        or message.author == message.guild.owner
                    ):
                        return

                    await message.author.kick()

                await modlog.create_case(
                    guild=message.guild,
                    bot=self.bot,
                    created_at=datetime.datetime.utcnow(),
                    action_type="phish_kicked",
                    user=message.author,
                    moderator=message.guild.me,
                    reason=f"Sent a malicious URL **`{domain}`** in the server",
                )
                kicks = await self.config.guild(message.guild).kicks()
                await self.config.guild(message.guild).kicks.set(kicks + 1)
        elif action == "ban":
            if (
                message.channel.permissions_for(message.guild.me).ban_members
                and message.channel.permissions_for(message.guild.me).manage_messages
            ):
                with contextlib.suppress(discord.NotFound):
                    await message.delete()
                    if (
                        message.author.top_role >= message.guild.me.top_role
                        or message.author == message.guild.owner
                    ):
                        return

                    await message.author.ban()

                await modlog.create_case(
                    guild=message.guild,
                    bot=self.bot,
                    created_at=datetime.datetime.utcnow(),
                    action_type="phish_banned",
                    user=message.author,
                    moderator=message.guild.me,
                    reason=f"Sent a malicious URL **`{domain}`** in the server",
                )
                bans = await self.config.guild(message.guild).bans()
                await self.config.guild(message.guild).bans.set(bans + 1)

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        """
        Handles the logic for checking URLs.
        """

        if not message.guild or message.author.bot:
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        links = self.get_links(message.content)
        if not links:
            return

        for url in links:
            domain = urlparse(url).netloc
            if domain in self.domains:
                await self.handle_phishing(message, domain)
                return

    @commands.command(
        aliases=["checkforphish", "checkscam", "checkforscam", "checkphishing"]
    )
    @commands.bot_has_permissions(embed_links=True)
    async def checkphish(self, ctx: Context, url: str = None):
        """
        Check if a url is a phishing scam.

        You can either provide a url or reply to a message containing a url.
        """
        if not url and not ctx.message.reference:
            return await ctx.send_help()

        if not url:
            try:
                m = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                await ctx.send_help()
                return
            url = m.content

        url = url.strip("<>")
        if not (url.startswith("http://") or url.startswith("https://")):
            embed = discord.Embed(
                title='Error: Invalid URL',
                description="The URL must start with `http://` or `https://`.\n\nPlease provide a properly formatted URL and try again.",
                colour=16729413,
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle.png")
            await ctx.send(embed=embed)
            return

        urls = self.extract_urls(url)
        if not urls:
            embed = discord.Embed(
                title='Error: Invalid URL',
                description="You provided an invalid URL.\n\nCheck the formatting of any links and try again...",
                colour=16729413,
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle.png")
            await ctx.send(embed=embed)
            return

        real_url = urls[0]
        domain = urlparse(real_url).netloc

        if domain in self.domains:
            embed = discord.Embed(
                title="Link query: Detected!",
                description="**This is a known dangerous website!**\n\nThis website is blocklisted for malicious behavior or content.",
                colour=16729413,
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle.png")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Link query: No detections",
                description="**This link looks clean.**\n\nYou should be able to proceed safely. Apply caution to your best judgement while browsing this site, and leave the site if at any time your sense of trust is impaired.",
                colour=2866574,
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Green/checkmark-circle.png")
            await ctx.send(embed=embed)

    @commands.group(aliases=["antiphish"])
    @commands.guild_only()
    async def antiphishing(self, ctx: Context):
        """
        Settings to configure phishing protection in this server.
        """
    @commands.has_permissions(administrator=True)
    @antiphishing.command()
    async def action(self, ctx: Context, action: str):
        """
        Choose the action that occurs when a user sends a phishing scam.

        Options:
        **`ignore`** - Disables phishing protection
        **`notify`** - Alerts in channel when malicious links detected (default)
        **`delete`** - Deletes the message
        **`kick`** - Delete message and kick sender
        **`ban`** - Delete message and ban sender (recommended)
        """
        valid_actions = ["ignore", "notify", "delete", "kick", "ban"]
        if action not in valid_actions:
            embed = discord.Embed(
                title='Error: Invalid action',
                description=(
                    "You provided an invalid action. You are able to choose any of the following actions to occur when a malicious link is detected...\n\n"
                    "`ignore` - Disables phishing protection\n"
                    "`notify` - Alerts in channel when malicious links detected (default)\n"
                    "`delete` - Deletes the message\n"
                    "`kick` - Delete message and kick sender\n"
                    "`ban` - Delete message and ban sender (recommended)\n\n"
                    "Retry that command with one of the above options."
                ),
                colour=16729413,
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle.png")
            await ctx.send(embed=embed)
            return

        await self.config.guild(ctx.guild).action.set(action)
        descriptions = {
            "ignore": "Phishing protection is now **disabled**. Malicious links will not trigger any actions.",
            "notify": "Malicious links will now trigger a **notification** in the channel when detected.",
            "delete": "Malicious links will now be **deleted** from conversation when detected.",
            "kick": "Malicious links will be **deleted** and the sender will be **kicked** when detected.",
            "ban": "Malicious links will be **deleted** and the sender will be **banned** when detected."
        }
        colours = {
            "ignore": 0xffd966,  # Yellow
            "notify": 0xffd966,  # Yellow
            "delete": 0xff4545,  # Red
            "kick": 0xff4545,  # Red
            "ban": 0xff4545  # Red
        }
        
        thumbnail_urls = {
            "ignore": "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/close.png",
            "notify": "https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/notifications.png",
            "delete": "https://www.beehive.systems/hubfs/Icon%20Packs/Red/trash.png",
            "kick": "https://www.beehive.systems/hubfs/Icon%20Packs/Red/footsteps.png",
            "ban": "https://www.beehive.systems/hubfs/Icon%20Packs/Red/ban.png"
        }

        description = descriptions[action]
        colour = colours[action]
        thumbnail_url = thumbnail_urls[action]

        embed = discord.Embed(title='Settings changed', description=description, colour=colour)
        embed.set_thumbnail(url=thumbnail_url)
        await ctx.send(embed=embed)

    @antiphishing.command()
    async def stats(self, ctx: Context):
        """
        Check protection statistics for this server
        """
        caught = await self.config.guild(ctx.guild).caught()
        notifications = await self.config.guild(ctx.guild).notifications()
        deletions = await self.config.guild(ctx.guild).deletions()
        kicks = await self.config.guild(ctx.guild).kicks()
        bans = await self.config.guild(ctx.guild).bans()
        last_updated = self.__last_updated__
        
        s_caught = "s" if caught != 1 else ""
        s_notifications = "s" if notifications != 1 else ""
        s_deletions = "s" if deletions != 1 else ""
        s_kicks = "s" if kicks != 1 else ""
        s_bans = "s" if bans != 1 else ""
        
        last_updated_str = f"**Last updated** **`{last_updated}`**"
        
        embed = discord.Embed(
            title='Protection statistics', 
            description=(
                f"Since being activated in {ctx.guild.name}, we've been hard at work.\n\n"
                f"- We've detected **`{caught}`** malicious link{s_caught} shared in chats\n"
                f"- We've warned you of danger **`{notifications}`** time{s_notifications}\n"
                f"- We've removed **`{deletions}`** message{s_deletions} to protect the community\n"
                f"- We've removed a user from the server **`{kicks}`** time{s_kicks}\n"
                f"- We've delivered **`{bans}`** permanent ban{s_bans} for sharing dangerous links\n\n"
                f"{last_updated_str}\n"
                f"**Version** **`{self.__version__}`**"
            ), 
            colour=16767334,
        )
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/shield-checkmark.png")
        view = discord.ui.View()
        button = discord.ui.Button(label="Learn More", url="https://www.beehive.systems")
        view.add_item(button)
        await ctx.send(embed=embed, view=view)

    @antiphishing.command()
    @commands.has_permissions(administrator=True)
    async def maxlinks(self, ctx: Context, max_links: int):
        """
        Set the maximum number of malicious links a user can share before being banned.
        """
        if max_links < 1:
            embed = discord.Embed(
                title='Error: Invalid number',
                description="The maximum number of malicious links must be at least 1.",
                colour=16729413,
            )
            embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Red/close-circle.png")
            await ctx.send(embed=embed)
            return

        await self.config.guild(ctx.guild).max_links.set(max_links)
        embed = discord.Embed(
            title='Settings changed',
            description=f"The maximum number of malicious links a user can share before being banned is now set to **{max_links}**.",
            colour=0xffd966,
        )
        embed.set_thumbnail(url="https://www.beehive.systems/hubfs/Icon%20Packs/Yellow/notifications.png")
        await ctx.send(embed=embed)
