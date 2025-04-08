import discord
from redbot.core import commands
from shazamio import Shazam

class ShazamCog(commands.Cog):
    """Cog to interact with the Shazam API using shazamio."""

    def __init__(self, bot):
        self.bot = bot
        self.shazam = Shazam()

    @commands.command(name="identify")
    async def identify_song(self, ctx: commands.Context, url: str = None):
        """Identify a song from an audio URL or uploaded file."""
        if not url and not ctx.message.attachments:
            await ctx.send("Please provide a URL or upload an audio file.", delete_after=10)
            return

        async with ctx.typing():
            try:
                if ctx.message.attachments:
                    attachment = ctx.message.attachments[0]
                    url = attachment.url

                track_info = await self.shazam.recognize_song(url)
                if track_info:
                    track_title = track_info['track']['title']
                    track_artist = track_info['track']['subtitle']
                    embed = discord.Embed(
                        title="Song Identified",
                        description=f"**Title:** {track_title}\n**Artist:** {track_artist}",
                        color=discord.Color.blue()
                    )
                else:
                    embed = discord.Embed(
                        title="Song Not Identified",
                        description="Could not identify the song from the provided URL or file.",
                        color=discord.Color.red()
                    )
            except Exception as e:
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occurred: {str(e)}",
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed)
