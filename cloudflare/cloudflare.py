import discord #type: ignore
import asyncio
import time
import tempfile
from datetime import datetime
from PIL import Image #type: ignore
from redbot.core import commands, Config #type: ignore
import aiohttp #type: ignore
import ipaddress
import json
import re
import io

class Cloudflare(commands.Cog):
    """A Red-Discordbot cog to interact with the Cloudflare API."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_global = {
            "api_key": None,
            "email": None,
            "bearer_token": None,
            "account_id": None,
        }
        self.config.register_global(**default_global)
        self.session = aiohttp.ClientSession()
    


    @commands.is_owner()
    @commands.group()
    async def images(self, ctx):
        """Cloudflare Images provides an end-to-end solution to build and maintain your image infrastructure from one API. Learn more at https://developers.cloudflare.com/images/"""
        
    @commands.is_owner()
    @images.command(name="upload")
    async def upload_image(self, ctx):
        """Upload an image to Cloudflare Images."""
        if not ctx.message.attachments:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Please attach an image to upload.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        attachment = ctx.message.attachments[0]
        if not attachment.filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'webp')):
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Please upload a valid image file (png, jpg, jpeg, gif, webp).",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")
        if not account_id or not bearer_token:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Account ID or bearer token not set.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}"
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1"

        try:
            async with self.session.get(attachment.url) as resp:
                if resp.status != 200:
                    await ctx.send(embed=discord.Embed(
                        title="Error",
                        description="Failed to download the image.",
                        color=discord.Color.from_str("#ff4545")
                    ))
                    return
                data = aiohttp.FormData()
                data.add_field('file', await resp.read(), filename=attachment.filename, content_type=attachment.content_type)

                # aiohttp.FormData automatically sets the correct Content-Type with boundary
                async with self.session.post(url, headers=headers, data=data) as response:
                    data = await response.json()
                    if not data.get("success", False):
                        error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                        embed = discord.Embed(
                            title="Failed to Upload Image",
                            description=f"**Error:** {error_message}",
                            color=discord.Color.from_str("#ff4545"))
                        await ctx.send(embed=embed)
                        return

                    result = data.get("result", {})
                    filename = result.get("filename", "Unknown")
                    image_id = result.get("id", "Unknown")
                    uploaded = result.get("uploaded", "Unknown")
                    variants = result.get("variants", [])

                    embed = discord.Embed(
                        title="Uploaded successfully",
                        color=discord.Color.from_str("#2BBD8E"))
                    embed.add_field(name="Filename", value=f"**`{filename}`**", inline=False)
                    embed.add_field(name="Uploaded", value=f"**`{uploaded}`**", inline=False)
                    embed.add_field(name="ID", value=f"```{image_id}```", inline=False)
                    for variant in variants:
                        embed.add_field(name="Variant", value=variant, inline=False)

                    await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @images.command(name="delete")
    async def delete_image(self, ctx, image_id: str):
        """Delete an image from Cloudflare Images by its ID."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")
        if not account_id or not bearer_token:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Account ID or bearer token not set.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1/{image_id}"

        try:
            async with self.session.delete(url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Delete Image",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545"))
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(
                    title="Deleted successfully",
                    description=f"Image with ID `{image_id}` has been deleted.",
                    color=discord.Color.from_str("#2BBD8E"))
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @images.command(name="info")
    async def image_info(self, ctx, image_id: str):
        """Get information about a specific image."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")
        if not account_id or not bearer_token:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Account ID or bearer token not set.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1/{image_id}"

        try:
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Fetch Image Info",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                result = data.get("result", {})
                filename = result.get("filename", "Unknown")
                upload_time = result.get("uploaded", "Unknown")
                variants = result.get("variants", [])

                embed = discord.Embed(
                    title="Image Information",
                    description=f"Information for image ID `{image_id}`:",
                    color=discord.Color.from_str("#2BBD8E")
                )
                embed.add_field(name="Filename", value=f"**`{filename}`**", inline=False)
                embed.add_field(name="Uploaded", value=f"**`{upload_time}`**", inline=False)
                for variant in variants:
                    embed.add_field(name="Variant", value=variant, inline=False)

                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @images.command(name="list")
    async def list_images(self, ctx):
        """List available images."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")
        if not account_id or not bearer_token:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Account ID or bearer token not set.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v2"

        try:
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Fetch Images",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                images = data.get("result", {}).get("images", [])
                if not images:
                    await ctx.send(embed=discord.Embed(
                        title="No Images Found",
                        description="No images found.",
                        color=discord.Color.from_str("#ff4545")
                    ))
                    return

                embed = discord.Embed(
                    title="Available Images",
                    description="Here are the available images:",
                    color=discord.Color.from_str("#2BBD8E")
                )

                for image in images:
                    filename = image.get("filename", "Unknown")
                    image_id = image.get("id", "Unknown")
                    upload_time = image.get("uploaded", "Unknown")
                    variants = image.get("variants", [])

                    embed.add_field(
                        name=f"Image ID: {image_id}",
                        value=f"**Filename:** `{filename}`\n**Uploaded:** `{upload_time}`\n**Variants:** {', '.join(variants)}",
                        inline=False
                    )

                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @images.command(name="stats")
    async def image_stats(self, ctx):
        """Fetch Cloudflare Images usage statistics."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")
        if not account_id or not bearer_token:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Account ID or bearer token not set.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/images/v1/stats"

        try:
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Fetch Image Stats",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                result = data.get("result", {})
                count = result.get("count", {})
                allowed = count.get("allowed", "Unknown")
                current = count.get("current", "Unknown")

                embed = discord.Embed(
                    title="Usage statistics",
                    description="Here are your current usage statistics for Cloudflare Images:",
                    color=discord.Color.from_str("#2BBD8E"))
                embed.add_field(name="Allowed", value=f"**`{allowed}`**", inline=True)
                embed.add_field(name="Current", value=f"**`{current}`**", inline=True)

                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @commands.group()
    async def loadbalancing(self, ctx):
        """Cloudflare Load Balancing distributes traffic across your servers, which reduces server strain and latency and improves the experience for end users. Learn more at https://developers.cloudflare.com/load-balancing/"""

    @commands.is_owner()
    @loadbalancing.command(name="create")
    async def loadbalancing_create(self, ctx, name: str, description: str, default_pools: str, country_pools: str, pop_pools: str, region_pools: str, proxied: bool, ttl: int, adaptive_routing: bool, failover_across_pools: bool, fallback_pool: str, location_strategy_mode: str, location_strategy_prefer_ecs: str, random_steering_default_weight: float, random_steering_pool_weights: str, steering_policy: str, session_affinity: str, session_affinity_ttl: int):
        """Create a new load balancer for a specific zone."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        zone_id = api_tokens.get("zone_id")
        if not bearer_token or not zone_id:
            embed = discord.Embed(
                title="Error",
                description="Bearer token or zone identifier not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/load_balancers"

        payload = {
            "name": name,
            "description": description,
            "default_pools": default_pools.split(","),
            "country_pools": {k: v.split(",") for k, v in (item.split(":") for item in country_pools.split(";"))},
            "pop_pools": {k: v.split(",") for k, v in (item.split(":") for item in pop_pools.split(";"))},
            "region_pools": {k: v.split(",") for k, v in (item.split(":") for item in region_pools.split(";"))},
            "proxied": proxied,
            "ttl": ttl,
            "adaptive_routing": {"enabled": adaptive_routing},
            "failover_across_pools": failover_across_pools,
            "fallback_pool": fallback_pool,
            "location_strategy": {
                "mode": location_strategy_mode,
                "prefer_ecs": location_strategy_prefer_ecs
            },
            "random_steering": {
                "default_weight": random_steering_default_weight,
                "pool_weights": {k: float(v) for k, v in (item.split(":") for item in random_steering_pool_weights.split(";"))}
            },
            "steering_policy": steering_policy,
            "session_affinity": session_affinity,
            "session_affinity_attributes": {
                "session_affinity_ttl": session_affinity_ttl
            }
        }

        try:
            async with self.session.post(url, headers=headers, json=payload) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Create Load Balancer",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                result = data.get("result", {})
                lb_id = result.get("id", "Unknown")
                lb_name = result.get("name", "Unknown")
                lb_created_on = result.get("created_on", "Unknown")

                embed = discord.Embed(
                    title="Load Balancer Created",
                    description=f"Load balancer **{lb_name}** has been successfully created.\n\n**ID:** {lb_id}\n**Created On:** {lb_created_on}",
                    color=discord.Color.from_str("#2BBD8E")
                )
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @loadbalancing.command(name="list")
    async def loadbalancing_list(self, ctx):
        """Get a list of load balancers for a specific zone."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        zone_id = api_tokens.get("zone_id")
        if not bearer_token or not zone_id:
            embed = discord.Embed(
                title="Error",
                description="Bearer token or zone identifier not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/load_balancers"

        try:
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Fetch Load Balancers",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                result = data.get("result", [])
                if not result:
                    embed = discord.Embed(
                        title="No Load Balancers Found",
                        description="There are no load balancers configured for this zone.",
                        color=discord.Color.from_str("#2BBD8E")
                    )
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(
                    title="Load Balancers",
                    description="Here is a list of load balancers for your Cloudflare zone:",
                    color=discord.Color.from_str("#2BBD8E")
                )
                for lb in result:
                    lb_name = lb.get("name", "Unknown")
                    lb_id = lb.get("id", "Unknown")
                    lb_status = "Enabled" if lb.get("enabled", False) else "Disabled"
                    embed.add_field(name=lb_name, value=f"ID: `{lb_id}`\nStatus: `{lb_status}`", inline=False)

                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @loadbalancing.command(name="delete")
    async def delete_load_balancer(self, ctx, load_balancer_id: str):
        """Delete a load balancer by its ID."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        zone_id = api_tokens.get("zone_id")
        if not bearer_token or not zone_id:
            embed = discord.Embed(
                title="Error",
                description="Bearer token or zone identifier not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/load_balancers/{load_balancer_id}"

        try:
            async with self.session.delete(url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Delete Load Balancer",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(
                    title="Load Balancer Deleted",
                    description=f"Load balancer with ID `{load_balancer_id}` has been successfully deleted.",
                    color=discord.Color.from_str("#2BBD8E")
                )
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @loadbalancing.command(name="info")
    async def get_load_balancer_info(self, ctx, load_balancer_id: str):
        """Get information about a specific load balancer by its ID."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        zone_id = api_tokens.get("zone_id")
        if not bearer_token or not zone_id:
            embed = discord.Embed(
                title="Error",
                description="Bearer token or zone identifier not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/load_balancers/{load_balancer_id}"

        try:
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Fetch Load Balancer Info",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                result = data.get("result", {})
                embed = discord.Embed(
                    title="Load Balancer Information",
                    description=f"Information for Load Balancer with ID `{load_balancer_id}`",
                    color=discord.Color.from_str("#2BBD8E")
                )
                embed.add_field(name="Name", value=f"**`{result.get('name', 'Unknown')}`**", inline=True)
                embed.add_field(name="Description", value=f"**`{result.get('description', 'None')}`**", inline=True)
                embed.add_field(name="Enabled", value=f"**`{result.get('enabled', 'Unknown')}`**", inline=True)
                embed.add_field(name="Created On", value=f"**`{result.get('created_on', 'Unknown')}`**", inline=True)
                embed.add_field(name="Modified On", value=f"**`{result.get('modified_on', 'Unknown')}`**", inline=True)
                embed.add_field(name="Proxied", value=f"**`{result.get('proxied', 'Unknown')}`**", inline=True)
                embed.add_field(name="Session Affinity", value=f"**`{result.get('session_affinity', 'None')}`**", inline=True)
                embed.add_field(name="Steering Policy", value=f"**`{result.get('steering_policy', 'None')}`**", inline=True)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @loadbalancing.command(name="patch")
    async def patch_load_balancer(self, ctx, load_balancer_id: str, key: str, value: str):
        """Update the settings of a specific load balancer."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        zone_id = api_tokens.get("zone_id")
        if not bearer_token or not zone_id:
            embed = discord.Embed(
                title="Error",
                description="Bearer token or zone identifier not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/load_balancers/{load_balancer_id}"
        payload = {
            key: value
        }

        try:
            async with self.session.patch(url, headers=headers, json=payload) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Update Load Balancer",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(
                    title="Load Balancer Updated",
                    description=f"Load Balancer with ID `{load_balancer_id}` has been updated successfully.",
                    color=discord.Color.from_str("#2BBD8E")
                )
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            ))

    @commands.is_owner()
    @commands.group()
    async def dnssec(self, ctx):
        """DNSSEC info"""

    @commands.is_owner()
    @dnssec.command(name="status")
    async def dnssec_status(self, ctx):
        """Get the current DNSSEC status and config for a specific zone."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        zone_id = api_tokens.get("zone_id")
        if not bearer_token or not zone_id:
            embed = discord.Embed(
                title="Error",
                description="Bearer token or zone identifier not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dnssec"

        try:
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Fetch DNSSEC Status",
                        description=f"**Error:** {error_message}",
                        color=discord.Color.from_str("#ff4545")
                    )
                    await ctx.send(embed=embed)
                    return

                result = data.get("result", {})
                embed = discord.Embed(
                    title="DNSSEC Status",
                    description=f"Here is the current DNSSEC status and configuration for Cloudflare Zone `{zone_id}`\n\nChange your zone using `[p]set api cloudflare zone_id`",
                    color=discord.Color.from_str("#2BBD8E")
                )
                embed.add_field(name="Algorithm", value=f"**`{result.get('algorithm', 'Unknown')}`**", inline=True)
                embed.add_field(name="Digest Algorithm", value=f"**`{result.get('digest_algorithm', 'Unknown')}`**", inline=True)
                embed.add_field(name="Digest Type", value=f"**`{result.get('digest_type', 'Unknown')}`**", inline=True)
                embed.add_field(name="Multi Signer", value=f"**`{str(result.get('dnssec_multi_signer', 'Unknown')).upper()}`**", inline=True)
                embed.add_field(name="Presigned", value=f"**`{str(result.get('dnssec_presigned', 'Unknown')).upper()}`**", inline=True)
                embed.add_field(name="Flags", value=f"**`{result.get('flags', 'Unknown')}`**", inline=True)
                embed.add_field(name="Key Tag", value=f"**`{result.get('key_tag', 'Unknown')}`**", inline=True)
                embed.add_field(name="Key Type", value=f"**`{result.get('key_type', 'Unknown')}`**", inline=True)
                modified_on = result.get('modified_on', 'Unknown')
                if modified_on != 'Unknown':
                    try:
                        from datetime import datetime
                        modified_on_dt = datetime.fromisoformat(modified_on.replace('Z', '+00:00'))
                        modified_on = f"<t:{int(modified_on_dt.timestamp())}:R>"
                    except ValueError:
                        pass
                embed.add_field(name="Modified On", value=f"**{modified_on}**", inline=True)
                status = result.get('status', 'Unknown').lower()
                if status == 'active':
                    status_display = "**`ACTIVE`**"
                elif status == 'pending':
                    status_display = "**`PENDING ACTIVATION`**"
                elif status == 'disabled':
                    status_display = "**`DISABLED`**"
                elif status == 'pending-disabled':
                    status_display = "**`PENDING DEACTIVATION`**"
                elif status == 'error':
                    status_display = "**`ERROR`**"
                else:
                    status_display = "**`UNKNOWN`**"
                embed.add_field(name="Status", value=status_display, inline=True)
                embed.add_field(name="DS", value=f"```{result.get('ds', 'Unknown')}```", inline=False)
                embed.add_field(name="Public Key", value=f"```{result.get('public_key', 'Unknown')}```", inline=False)
                embed.add_field(name="Digest", value=f"```{result.get('digest', 'Unknown')}```", inline=False)

                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @dnssec.command(name="delete")
    async def delete_dnssec(self, ctx):
        """Delete DNSSEC on the currently set Cloudflare zone"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        zone_id = api_tokens.get("zone_id")
        if not zone_id:
            embed = discord.Embed(title="Error", description="Zone ID not set.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {api_tokens.get('bearer_token')}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dnssec"
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                data = await response.json()
                if data.get("success"):
                    embed = discord.Embed(
                        title="Success",
                        description="DNSSEC has been successfully deleted for the set zone.",
                        color=discord.Color.from_str("#2BBD8E")
                    )
                else:
                    error_messages = "\n".join([error.get("message", "Unknown error") for error in data.get("errors", [])])
                    embed = discord.Embed(
                        title="Error",
                        description=f"Failed to delete DNSSEC: {error_messages}",
                        color=discord.Color.from_str("#ff4545")
                    )
                await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.group(invoke_without_command=True)
    async def keystore(self, ctx):
        """Fetch keys in use for development purposes only"""

    @commands.is_owner()
    @keystore.command(name="email")
    async def email(self, ctx):
        """Fetch the current Cloudflare email"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        if not email:
            embed = discord.Embed(title="Error", description="Email not set.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare email**\n\n```{email}```")
            embed = discord.Embed(title="Success", description="The Cloudflare email has been sent to your DMs.", color=discord.Color.from_str("#2BBD8E"))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)

    @commands.is_owner()
    @keystore.command(name="apikey")
    async def api_key(self, ctx):
        """Fetch the current Cloudflare API key"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        if not api_key:
            embed = discord.Embed(title="Error", description="API key not set.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare API key**\n\n```{api_key}```")
            embed = discord.Embed(title="Success", description="The Cloudflare API key has been sent to your DMs.", color=discord.Color.from_str("#2BBD8E"))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)

    @commands.is_owner()
    @keystore.command(name="bearertoken")
    async def bearer_token(self, ctx):
        """Fetch the current Cloudflare bearer token"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        if not bearer_token:
            embed = discord.Embed(title="Error", description="Bearer token not set.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare bearer token**\n\n```{bearer_token}```")
            embed = discord.Embed(title="Success", description="The Cloudflare bearer token has been sent to your DMs.", color=discord.Color.from_str("#2BBD8E"))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)

    @commands.is_owner()
    @keystore.command(name="accountid")
    async def account_id(self, ctx):
        """Fetch the current Cloudflare account ID"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        if not account_id:
            embed = discord.Embed(title="Error", description="Account ID not set.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare Account ID**\n\n```{account_id}```")
            embed = discord.Embed(title="Success", description="The Cloudflare Account ID has been sent to your DMs.", color=discord.Color.from_str("#2BBD8E"))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)

    @commands.is_owner()
    @keystore.command(name="zoneid")
    async def zone_id(self, ctx):
        """Fetch the current Cloudflare zone ID"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        zone_id = api_tokens.get("zone_id")
        if not zone_id:
            embed = discord.Embed(title="Error", description="Zone ID not set.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)
            return

        try:
            await ctx.author.send(f"**Current Cloudflare Zone ID**\n\n```{zone_id}```")
            embed = discord.Embed(title="Success", description="The Cloudflare Zone ID has been sent to your DMs.", color=discord.Color.from_str("#2BBD8E"))
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(title="Error", description="I couldn't send you a DM. Please check your DM settings.", color=discord.Color.from_str("#ff4545"))
            await ctx.send(embed=embed)

    @commands.is_owner()
    @commands.group()
    async def botmanagement(self, ctx):
        """Cloudflare bot solutions identify and mitigate automated traffic to protect your domain from bad bots. Learn more at https://developers.cloudflare.com/bots/"""

    @commands.is_owner()
    @botmanagement.command(name="get")
    async def get_bot_management_config(self, ctx):
        """Get the current bot management config from Cloudflare."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        zone_id = api_tokens.get("zone_id")
        
        if not api_key or not email or not zone_id:
            embed = discord.Embed(
                title="Error",
                description="API key, email, or zone ID not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/bot_management"
        
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch bot management config: {response.status}",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            bot_management_config = data.get("result", {})
            if not bot_management_config:
                embed = discord.Embed(
                    title="Error",
                    description="No bot management config found.",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="Bot Management",
                description="Your current **Cloudflare Bot Management** settings are as follows:",
                color=discord.Color.from_str("#2BBD8E")
            )

            def format_value(value):
                return value.upper() if isinstance(value, str) else str(value).upper()

            # Add fields to the embed only if the corresponding key is present in the API response
            if 'fight_mode' in bot_management_config:
                embed.add_field(name="Super Bot Fight Mode", value=f"**`{format_value(bot_management_config.get('fight_mode', 'Not set'))}`**", inline=False)
            if 'enable_js' in bot_management_config:
                embed.add_field(name="Enable JS", value=f"**`{format_value(bot_management_config.get('enable_js', 'Not set'))}`**", inline=False)
            if 'using_latest_model' in bot_management_config:
                embed.add_field(name="Using Latest Model", value=f"**`{format_value(bot_management_config.get('using_latest_model', 'Not set'))}`**", inline=False)
            if 'optimize_wordpress' in bot_management_config:
                embed.add_field(name="Optimize Wordpress", value=f"**`{format_value(bot_management_config.get('optimize_wordpress', 'Not set'))}`**", inline=False)
            if 'sbfm_definitely_automated' in bot_management_config:
                embed.add_field(name="Definitely Automated", value=f"**`{format_value(bot_management_config.get('sbfm_definitely_automated', 'Not set'))}`**", inline=True)
            if 'sbfm_verified_bots' in bot_management_config:
                embed.add_field(name="Verified Bots", value=f"**`{format_value(bot_management_config.get('sbfm_verified_bots', 'Not set'))}`**", inline=True)
            if 'sbfm_static_resource_protection' in bot_management_config:
                embed.add_field(name="Static Resource Protection", value=f"**`{format_value(bot_management_config.get('sbfm_static_resource_protection', 'Not set'))}`**", inline=True)
            if 'suppress_session_score' in bot_management_config:
                embed.add_field(name="Suppress Session Score", value=f"**`{format_value(bot_management_config.get('suppress_session_score', 'Not set'))}`**", inline=False)
            if 'auto_update_model' in bot_management_config:
                embed.add_field(name="Auto Update Model", value=f"**`{format_value(bot_management_config.get('auto_update_model', 'Not set'))}`**", inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @botmanagement.command(name="update")
    async def update_bot_management_config(self, ctx, setting: str, value: str):
        """Update a specific bot management setting."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        zone_id = api_tokens.get("zone_id")
        bearer_token = api_tokens.get("bearer_token")
        if not api_key or not email or not zone_id:
            embed = discord.Embed(
                title="Error",
                description="API key, email, or zone ID not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/bot_management"
        payload = json.dumps({setting: value.lower() == 'true'})

        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=headers, data=payload) as response:
                    data = await response.json()
                    if response.status != 200:
                        error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                        embed = discord.Embed(
                            title="Failed to Update Bot Management Config",
                            description=f"**Error:** {error_message}",
                            color=discord.Color.from_str("#ff4545")
                        )
                        await ctx.send(embed=embed)
                        return

                    embed = discord.Embed(
                        title="Bot management changed",
                        description=f"Successfully updated bot management setting **`{setting}`** to **`{value}`**.",
                        color=discord.Color.from_str("#2BBD8E")
                    )
                    await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}\n\nRequest URL: {url}\nHeaders: {headers}\nPayload: {payload}",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.author.send(embed=embed)

    @commands.is_owner()
    @commands.group()
    async def zones(self, ctx):
        """Cloudflare command group."""
        if ctx.invoked_subcommand is None:
            await ctx.send("Invalid Cloudflare command passed.")
        
    @commands.is_owner()
    @zones.command(name="get")
    async def get(self, ctx):
        """Get the list of zones from Cloudflare."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        if not api_key or not email:
            embed = discord.Embed(
                title="Error",
                description="API key or email not set.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json"
        }

        async with self.session.get("https://api.cloudflare.com/client/v4/zones", headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch zones: {response.status}",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            zones = data.get("result", [])
            if not zones:
                embed = discord.Embed(
                    title="Error",
                    description="No zones found.",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            zone_names = [zone["name"] for zone in zones]
            pages = [zone_names[i:i + 10] for i in range(0, len(zone_names), 10)]

            current_page = 0
            embed = discord.Embed(
                title="Zones in Cloudflare account",
                description="\n".join(pages[current_page]),
                color=discord.Color.from_str("#2BBD8E")
            )
            message = await ctx.send(embed=embed)

            if len(pages) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("❌")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "❌", "▶️"] and reaction.message.id == message.id

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

                        if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                            current_page += 1
                            embed.description = "\n".join(pages[current_page])
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "◀️" and current_page > 0:
                            current_page -= 1
                            embed.description = "\n".join(pages[current_page])
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "❌":
                            await message.delete()
                            break

                    except asyncio.TimeoutError:
                        break

                # Remove reactions after timeout
                try:
                    await message.clear_reactions()
                except discord.Forbidden:
                    pass


    @commands.group(invoke_without_command=False)
    async def intel(self, ctx):
        """
        Utilize security & network intelligence powered by Cloudflare's global distributed network to assist in your investigations.
        
        Learn more at [cloudflare.com](<https://www.cloudflare.com/application-services/products/cloudforceone/>)
        """

    @intel.command(name="whois")
    async def whois(self, ctx, domain: str):
        """
        View available WHOIS info
        """

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(
                title="Configuration Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        async with self.session.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/whois?domain={domain}", headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch WHOIS information: {response.status}",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to fetch WHOIS information.",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            whois_info = data.get("result", {})

            # Check if the domain is found
            if whois_info.get("found", True) is False:
                embed = discord.Embed(
                    title="Domain not registered",
                    description="The domain doesn't seem to be registered. Please check the query and try again.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return

            pages = []
            page = discord.Embed(title=f"WHOIS query for {domain}", color=0xFF6633)
            page.set_footer(text="WHOIS information provided by Cloudflare", icon_url="https://cdn.brandfetch.io/idJ3Cg8ymG/w/400/h/400/theme/dark/icon.jpeg?c=1dxbfHSJFAPEGdCLU4o5B")
            field_count = 0

            def add_field_to_page(page, name, value):
                nonlocal field_count, pages
                page.add_field(name=name, value=value, inline=False)
                field_count += 1
                if field_count == 10:
                    pages.append(page)
                    page = discord.Embed(title=f"WHOIS query for {domain}", color=0xFF6633)
                    field_count = 0
                return page

            if "registrar" in whois_info:
                registrar_value = f"{whois_info['registrar']}"
                page.add_field(name="Registered with", value=registrar_value, inline=True)

            if "created_date" in whois_info:
                created_date = whois_info["created_date"]
                if isinstance(created_date, str):
                    from datetime import datetime
                    try:
                        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S")
                unix_timestamp = int(created_date.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
                discord_timestamp = f"<t:{unix_timestamp}:d>"
                page.add_field(name="Created on", value=discord_timestamp, inline=True)

            if "updated_date" in whois_info:
                try:
                    updated_date = int(datetime.strptime(whois_info["updated_date"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp())
                    page.add_field(name="Updated on", value=f"<t:{updated_date}:d>", inline=True)
                except ValueError:
                    pass
                except AttributeError:
                    pass

            if "expiration_date" in whois_info:
                expiration_date = whois_info["expiration_date"]
                if isinstance(expiration_date, str):
                    try:
                        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                    except ValueError:
                        expiration_date = datetime.strptime(expiration_date, "%Y-%m-%dT%H:%M:%S")
                unix_timestamp = int(expiration_date.timestamp())
                discord_timestamp = f"<t:{unix_timestamp}:d>"
                page.add_field(name="Expires on", value=discord_timestamp, inline=True)

            if "dnssec" in whois_info:
                dnssec_value = whois_info["dnssec"]
                if dnssec_value is True:
                    dnssec_value = ":white_check_mark: Enabled"
                elif dnssec_value is False:
                    dnssec_value = ":x: Disabled"
                else:
                    dnssec_value = f":grey_question: Unknown"
                page.add_field(name="DNSSEC", value=dnssec_value, inline=True)

            if "whois_server" in whois_info:
                whois_server = f"{whois_info['whois_server']}"
                page.add_field(name="Lookup via", value=whois_server, inline=True)

            if "nameservers" in whois_info:
                nameservers_list = "\n".join(f"- {ns}" for ns in whois_info["nameservers"])
                page = add_field_to_page(page, "Nameservers", nameservers_list)
                
            if "status" in whois_info:
                status_explainers = {
                    "clienttransferprohibited": ":lock: **Transfer prohibited**",
                    "clientdeleteprohibited": ":no_entry: **Deletion prohibited**",
                    "clientupdateprohibited": ":pencil2: **Update prohibited**",
                    "clientrenewprohibited": ":credit_card: **Renewal prohibited**",
                    "clienthold": ":pause_button: **Held by registrar**",
                    "servertransferprohibited": ":lock: **Server locked**",
                    "serverdeleteprohibited": ":no_entry: **Server deletion prohibited**",
                    "serverupdateprohibited": ":pencil2: **Server update prohibited**",
                    "serverhold": ":pause_button: **Server on hold**",
                    "pendingtransfer": ":hourglass: **Pending transfer**",
                    "pendingdelete": ":hourglass: **Pending deletion**",
                    "pendingupdate": ":hourglass: **Pending update**",
                    "ok": ":white_check_mark: **Active**"
                }
                status_list = "\n".join(
                    f"- `{status}` \n> {status_explainers.get(status.lower(), ':grey_question: *Unknown status*')}" 
                    for status in whois_info["status"]
                )
                page = add_field_to_page(page, "Status", status_list)

            contact_methods = []

            # Order: Name, Organization, ID, Email, Phone, Fax, Address
            if "registrar_name" in whois_info:
                contact_methods.append(f":office: {whois_info['registrar_name']}")
            if "registrar_org" in whois_info:
                contact_methods.append(f":busts_in_silhouette: {whois_info['registrar_org']}")
            if "registrar_id" in whois_info:
                contact_methods.append(f":id: {whois_info['registrar_id']}")
            if "registrar_email" in whois_info:
                contact_methods.append(f":incoming_envelope: {whois_info['registrar_email']}")
            if "registrar_phone" in whois_info:
                phone_number = whois_info['registrar_phone']
                contact_methods.append(f":telephone_receiver: {phone_number}")
            if "registrar_phone_ext" in whois_info:
                contact_methods.append(f":1234: {whois_info['registrar_phone_ext']}")
            if "registrar_fax" in whois_info:
                contact_methods.append(f":fax: {whois_info['registrar_fax']}")
            if "registrar_fax_ext" in whois_info:
                contact_methods.append(f":1234: {whois_info['registrar_fax_ext']}")
            if "registrar_street" in whois_info:
                contact_methods.append(f":house: {whois_info['registrar_street']}")
            if "registrar_province" in whois_info:
                contact_methods.append(f":map: {whois_info['registrar_province']}")
            if "registrar_postal_code" in whois_info:
                contact_methods.append(f":mailbox: {whois_info['registrar_postal_code']}")

            if contact_methods:
                contact_info = "\n".join(contact_methods)
                page = add_field_to_page(page, "To report abuse", contact_info)

            if page.fields:
                pages.append(page)

            # Create a view with buttons
            view = discord.ui.View()
            if "administrative_referral_url" in whois_info:
                button = discord.ui.Button(label="Admin", url=whois_info["administrative_referral_url"])
                view.add_item(button)
            if "billing_referral_url" in whois_info:
                button = discord.ui.Button(label="Billing", url=whois_info["billing_referral_url"])
                view.add_item(button)
            if "registrant_referral_url" in whois_info:
                button = discord.ui.Button(label="Registrant", url=whois_info["registrant_referral_url"])
                view.add_item(button)
            if "registrar_referral_url" in whois_info:
                button = discord.ui.Button(label="Visit registrar", url=whois_info["registrar_referral_url"])
                view.add_item(button)
            if "technical_referral_url" in whois_info:
                button = discord.ui.Button(label="Technical", url=whois_info["technical_referral_url"])
                view.add_item(button)            

            async def download_report(interaction: discord.Interaction):
                try:
                    html_content = f"""
                    <html>
                        <head>
                            <title>WHOIS Report for {domain}</title>
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <link rel="preconnect" href="https://fonts.googleapis.com">
                            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                            <link href="https://fonts.googleapis.com/css2?family=Inter+Tight:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
                            <style>
                                body {{
                                    font-family: 'Inter Tight', sans-serif;
                                    margin: 20px;
                                    background-color: #f4f4f9;
                                    color: #333;
                                }}
                                h1, h2, h3 {{
                                    color: #000000;
                                    text-align: left;
                                }}
                                h1 {{
                                    font-size: 2em;
                                    margin-bottom: 10px;
                                }}
                                h2 {{
                                    font-size: 1.5em;
                                    margin-bottom: 5px;
                                }}
                                h3 {{
                                    font-size: 1.2em;
                                    margin-bottom: 5px;
                                }}
                                .header {{
                                    text-align: left;
                                    margin-bottom: 30px;
                                }}
                                .content {{
                                    max-width: 800px;
                                    margin: 0 auto;
                                    padding: 20px;
                                    background-color: #ffffff;
                                    border-radius: 8px;
                                    box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
                                }}
                                .section {{
                                    margin-bottom: 20px;
                                }}
                                .card-container {{
                                    display: flex;
                                    flex-wrap: wrap;
                                    justify-content: space-between;
                                    gap: 10px; /* Add gap to ensure space between cards */
                                }}
                                .card {{
                                    background-color: #f0f4f9;
                                    border-radius: 10px;
                                    padding: 15px;
                                    margin-bottom: 10px;
                                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
                                    flex: 1 1 calc(50% - 10px); /* Ensure cards take up half the container width minus the gap */
                                    box-sizing: border-box; /* Include padding and border in the element's total width and height */
                                }}
                                .key {{
                                    font-weight: bold;
                                    color: #000000;
                                    font-size: 1em;
                                }}
                                .value {{
                                    color: #000000;
                                    font-size: 1em;
                                }}
                                hr {{
                                    border: 0;
                                    height: 1px;
                                    background: #ddd;
                                    margin: 20px 0;
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="content">
                                <div class="header">
                                    <h1>WHOIS Report for {domain}</h1>
                                    <p>Data provided by Cloudflare Intel and the respective registrar's WHOIS server</p>
                                </div>
                                <hr>
                                <div class="section">
                                    <h2>Report information</h2>
                                    <div class="card">
                                        <p><span class="key">Domain queried</span></p>
                                        <p><span class="value">{domain}</span></p>
                                    </div>
                                </div>
                                <div class="section">
                                    <h2>WHOIS</h2>
                                    <div class="card-container">
                    """
                    for key, value in whois_info.items():
                        html_content += f"""
                                        <div class='card'>
                                            <p><span class='key'>{key.replace('_', ' ').title()}</span></p>
                                            <p><span class='value'>{value}</span></p>
                                        </div>
                        """

                    html_content += """
                                    </div>
                                </div>
                            </div>
                        </body>
                    </html>
                    """

                    # Use a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as temp_file:
                        temp_file.write(html_content.encode('utf-8'))
                        temp_file_path = temp_file.name

                    # Send the HTML file
                    await interaction.response.send_message(
                        content="Please open the attached file in a web browser to view the report.",
                        file=discord.File(temp_file_path),
                        ephemeral=True
                    )
                except Exception as e:
                    await interaction.response.send_message(
                        content="Failed to generate or send the HTML report.",
                        ephemeral=True
                    )

            download_button = discord.ui.Button(label="Download full report", style=discord.ButtonStyle.grey)
            download_button.callback = download_report
            view.add_item(download_button)

            message = await ctx.send(embed=pages[0], view=view)

            current_page = 0
            if len(pages) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("❌")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "❌", "▶️"] and reaction.message.id == message.id

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                        if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                            current_page += 1
                            await message.edit(embed=pages[current_page])
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "◀️" and current_page > 0:
                            current_page -= 1
                            await message.edit(embed=pages[current_page])
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "❌":
                            await message.delete()
                            break

                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        break

    @intel.command(name="domain")
    async def querydomain(self, ctx, domain: str):
        """View information about a domain"""
        
        # Check if the input is an IP address
        try:
            ip_obj = ipaddress.ip_address(domain)
            embed = discord.Embed(title="Error", description="The input appears to be an IP address. Please use the `ip` subcommand for IP address queries.", color=0xff4545)
            await ctx.send(embed=embed)
            return
        except ValueError:
            pass  # Not an IP address, continue with query

        # Fetch the blocklist from the web
        blocklist_url = "https://www.beehive.systems/hubfs/blocklist/blocklist.json"
        async with self.session.get(blocklist_url) as blocklist_response:
            if blocklist_response.status == 200:
                blocklist = await blocklist_response.json()
            else:
                embed = discord.Embed(title="Error", description="Failed to fetch the blocklist.", color=0xff4545)
                await ctx.send(embed=embed)
                return
        
        is_blocked = domain in blocklist

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/domain"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }
        params = {
            "domain": domain
        }

        async with self.session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            if response.status == 200 and data.get("success", False):
                result = data.get("result", {})
                embed = discord.Embed(title=f"Domain intelligence for {result.get('domain', 'N/A')}", color=0xFF6633)
                
                domain = result.get('domain')
                if domain:
                    embed.add_field(name="Domain", value=f"{domain}", inline=False)
                
                risk_score = result.get('risk_score')
                if risk_score is not None:
                    embed.add_field(name="Risk score", value=f"{risk_score}", inline=False)
                
                popularity_rank = result.get('popularity_rank')
                if popularity_rank is not None:
                    embed.add_field(name="Popularity rank", value=f"{popularity_rank}", inline=False)
                
                application = result.get("application", {})
                application_name = application.get('name')
                if application_name:
                    embed.add_field(name="Application", value=f"{application_name}", inline=False)
                
                additional_info = result.get("additional_information", {})
                suspected_malware_family = additional_info.get('suspected_malware_family')
                if suspected_malware_family:
                    embed.add_field(name="Suspected malware family", value=f"{suspected_malware_family}", inline=False)
                
                content_categories = result.get("content_categories", [])
                if content_categories:
                    categories_list = "\n".join([f"- {cat.get('name', 'N/A')}" for cat in content_categories])
                    embed.add_field(name="Content categories", value=categories_list, inline=False)
                
                resolves_to_refs = result.get("resolves_to_refs", [])
                if resolves_to_refs:
                    embed.add_field(name="Resolves to", value=", ".join([f"{ref.get('value', 'N/A')}" for ref in resolves_to_refs]), inline=False)
                
                inherited_content_categories = result.get("inherited_content_categories", [])
                if inherited_content_categories:
                    embed.add_field(name="Inherited content categories", value=", ".join([f"{cat.get('name', 'N/A')}" for cat in inherited_content_categories]), inline=False)
                
                inherited_from = result.get('inherited_from')
                if inherited_from:
                    embed.add_field(name="Inherited from", value=f"`{inherited_from}`", inline=False)
                
                inherited_risk_types = result.get("inherited_risk_types", [])
                if inherited_risk_types:
                    embed.add_field(name="Inherited risk types", value=", ".join([f"{risk.get('name', 'N/A')}" for risk in inherited_risk_types]), inline=False)
                
                risk_types = result.get("risk_types", [])
                if risk_types:
                    embed.add_field(name="Risk types", value=", ".join([f"{risk.get('name', 'N/A')}" for risk in risk_types]), inline=False)

                # Add blocklist status
                blocklist_status = ":white_check_mark: Yes" if is_blocked else ":x: No"
                embed.add_field(name="On BeeHive blocklist", value=f"{blocklist_status}", inline=False)

                # Create a view with a download button
                view = discord.ui.View()

                async def download_report(interaction: discord.Interaction):
                    try:
                        # Generate the report content
                        report_content = f"Domain Intelligence Report for {domain}\n\n"
                        report_content += f"Domain: {result.get('domain', 'N/A')}\n"
                        report_content += f"Risk Score: {result.get('risk_score', 'N/A')}\n"
                        report_content += f"Popularity Rank: {result.get('popularity_rank', 'N/A')}\n"
                        report_content += f"Application: {application.get('name', 'N/A')}\n"
                        report_content += f"Suspected Malware Family: {additional_info.get('suspected_malware_family', 'N/A')}\n"
                        report_content += f"Content Categories: {', '.join([cat.get('name', 'N/A') for cat in content_categories])}\n"
                        report_content += f"Resolves To: {', '.join([ref.get('value', 'N/A') for ref in resolves_to_refs])}\n"
                        report_content += f"Inherited Content Categories: {', '.join([cat.get('name', 'N/A') for cat in inherited_content_categories])}\n"
                        report_content += f"Inherited From: {result.get('inherited_from', 'N/A')}\n"
                        report_content += f"Inherited Risk Types: {', '.join([risk.get('name', 'N/A') for risk in inherited_risk_types])}\n"
                        report_content += f"Risk Types: {', '.join([risk.get('name', 'N/A') for risk in risk_types])}\n"
                        report_content += f"On BeeHive Blocklist: {'Yes' if is_blocked else 'No'}\n"

                        # Use a temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
                            temp_file.write(report_content.encode('utf-8'))
                            temp_file_path = temp_file.name

                        # Send the TXT file
                        await interaction.response.send_message(file=discord.File(temp_file_path))
                    except Exception as e:
                        await interaction.response.send_message(
                            content="Failed to generate or send the TXT report.",
                            ephemeral=True
                        )

                download_button = discord.ui.Button(label="Download full report", style=discord.ButtonStyle.grey)
                download_button.callback = download_report
                view.add_item(download_button)

                embed.set_footer(text="Data provided by BeeHive and Cloudflare")
                await ctx.send(embed=embed, view=view)
            else:
                error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message", "Unknown error")
                error_embed = discord.Embed(title="Error", description=f"Error: {error_message}", color=0xff4545)
                await ctx.send(embed=error_embed)

    @intel.command(name="ip")
    async def queryip(self, ctx, ip: str):
        """View information about an IP address"""

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/ip"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }
        params = {}
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.is_private:
                embed = discord.Embed(title="Local IP Address", description="The IP address you entered is a local IP address and cannot be queried.", color=0xff4545)
                await ctx.send(embed=embed)
                return
            if ip_obj.version == 4:
                params["ipv4"] = ip
            elif ip_obj.version == 6:
                params["ipv6"] = ip
        except ValueError:
            embed = discord.Embed(title="Error", description="Invalid IP address format.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        async with self.session.get(url, headers=headers, params=params) as response:
            data = await response.json()
            if response.status == 200 and data.get("success", False):
                result = data.get("result", [{}])[0]
                embed = discord.Embed(title=f"IP intelligence for {result.get('ip', 'N/A')}", color=0xFF6633)
                
                ip_value = result.get('ip')
                if ip_value:
                    embed.add_field(name="IP", value=f"{ip_value}", inline=True)
                
                belongs_to = result.get("belongs_to_ref", {})
                description = belongs_to.get('description')
                if description:
                    embed.add_field(name="Belongs to", value=f"{description}", inline=True)
                
                country = belongs_to.get('country')
                if country:
                    embed.add_field(name="Country", value=f"{country}", inline=True)
                
                type_value = belongs_to.get('type')
                if type_value:
                    embed.add_field(name="Type", value=f"{type_value.upper()}", inline=True)
                
                risk_types = result.get("risk_types", [])
                if risk_types:
                    risk_types_str = ", ".join([f"{risk.get('name', 'N/A')}" for risk in risk_types if risk.get('name')])
                    if risk_types_str:
                        embed.add_field(name="Risk types", value=risk_types_str, inline=True)
                
                if "ptr_lookup" in result and result["ptr_lookup"] and "ptr_domains" in result["ptr_lookup"] and result["ptr_lookup"]["ptr_domains"]:
                    ptr_domains = "\n".join([f"- {domain}" for domain in result["ptr_lookup"]["ptr_domains"]])
                    embed.add_field(name="PTR domains", value=ptr_domains, inline=True)
                
                result_info = data.get("result_info", {})
                total_count = result_info.get('total_count')
                if total_count:
                    embed.add_field(name="Total count", value=f"{total_count}", inline=False)
                
                page = result_info.get('page')
                if page:
                    embed.add_field(name="Page", value=f"{page}", inline=False)
                
                per_page = result_info.get('per_page')
                if per_page:
                    embed.add_field(name="Per page", value=f"{per_page}", inline=False)
                
                embed.set_footer(text="IP intelligence provided by Cloudflare")
                await ctx.send(embed=embed)
            else:
                error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message", "Unknown error")
                embed = discord.Embed(title="Error", description=f"Error: {error_message}", color=0xff4545)
                await ctx.send(embed=embed)

    @intel.command(name="domainhistory")
    async def domainhistory(self, ctx, domain: str):
        """
        View information about a domain's history
        """
        # Check if the input is an IP address
        try:
            ip_obj = ipaddress.ip_address(domain)
            embed = discord.Embed(title="Error", description="The input appears to be an IP address. Please use the `ip` subcommand for IP address queries.", color=0xff4545)
            await ctx.send(embed=embed)
            return
        except ValueError:
            pass  # Not an IP address, continue with query

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/domain-history"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }
        params = {"domain": domain}

        async with self.session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"] and data["result"]:
                    result = data["result"][0]
                    categorizations = result.get("categorizations", [])
                    pages = [categorizations[i:i + 5] for i in range(0, len(categorizations), 5)]
                    current_page = 0

                    def create_embed(page):
                        embed = discord.Embed(title=f"Domain history for {domain}", color=0xFF6633)
                        if "domain" in result:
                            embed.add_field(name="Domain", value=f"{result['domain']}", inline=True)
                        for categorization in page:
                            categories = ", ".join([f"- {category['name']}\n" for category in categorization["categories"]])
                            embed.add_field(name="Categories", value=categories, inline=True)
                            if "start" in categorization:
                                start_timestamp = discord.utils.format_dt(discord.utils.parse_time(categorization['start']), style='d')
                                embed.add_field(name="Beginning", value=f"{start_timestamp}", inline=True)
                            if "end" in categorization:
                                end_timestamp = discord.utils.format_dt(discord.utils.parse_time(categorization['end']), style='d')
                                embed.add_field(name="Ending", value=f"{end_timestamp}", inline=True)
                        return embed

                    message = await ctx.send(embed=create_embed(pages[current_page]))

                    if len(pages) > 1:
                        await message.add_reaction("◀️")
                        await message.add_reaction("❌")
                        await message.add_reaction("▶️")

                        def check(reaction, user):
                            return user == ctx.author and str(reaction.emoji) in ["◀️", "❌", "▶️"] and reaction.message.id == message.id

                        while True:
                            try:
                                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

                                if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                                    current_page += 1
                                    await message.edit(embed=create_embed(pages[current_page]))
                                    await message.remove_reaction(reaction, user)

                                elif str(reaction.emoji) == "◀️" and current_page > 0:
                                    current_page -= 1
                                    await message.edit(embed=create_embed(pages[current_page]))
                                    await message.remove_reaction(reaction, user)

                                elif str(reaction.emoji) == "❌":
                                    await message.delete()
                                    break

                            except asyncio.TimeoutError:
                                break

                        try:
                            await message.clear_reactions()
                        except discord.Forbidden:
                            pass
                else:
                    embed = discord.Embed(title="No data available", description="There is no domain history available for this domain. Please try this query again later, as results are subject to update.", color=0xff4545)
                    await ctx.send(embed=embed)
            elif response.status == 400:
                embed = discord.Embed(title="Bad Request", description="The server could not understand the request due to invalid syntax.", color=0xff4545)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Failed to query Cloudflare API", description=f"Status code: {response.status}", color=0xff4545)
                await ctx.send(embed=embed)

    @intel.command(name="asn")
    async def asnintel(self, ctx, asn: int):
        """
        View information about an ASN
        """
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/asn/{asn}"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }

        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"]
                    embed = discord.Embed(title=f"Intelligence for ASN#{asn}", color=0xFF6633)
                    
                    if "asn" in result:
                        embed.add_field(name="ASN Number", value=f"{result['asn']}", inline=True)
                    if "description" in result:
                        owner_query = result['description'].replace(' ', '+')
                        google_search_url = f"https://www.google.com/search?q={owner_query}"
                        embed.add_field(name="Owner", value=f"[{result['description']}]({google_search_url})", inline=True)
                    if "country" in result:
                        embed.add_field(name="Region", value=f":flag_{result['country'].lower()}: {result['country']}", inline=True)
                    if "type" in result:
                        embed.add_field(name="Type", value=f"{result['type'].capitalize()}", inline=True)
                    if "risk_score" in result:
                        embed.add_field(name="Risk score", value=f"{result['risk_score']}", inline=True)
                    embed.set_footer(text="ASN intelligence provided by Cloudflare")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Error", description=f"Error: {data['errors']}", color=0xff4545)
                    await ctx.send(embed=embed)
            elif response.status == 400:
                embed = discord.Embed(title="Bad Request", description="The server could not understand the request due to invalid syntax.", color=0xff4545)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Failed to query Cloudflare API", description=f"Status code: {response.status}", color=0xff4545)
                await ctx.send(embed=embed)

    @intel.command(name="subnets")
    async def asnsubnets(self, ctx, asn: int):
        """
        View information for ASN subnets
        """
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        # Check if any required token is missing
        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/intel/asn/{asn}/subnets"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }

        async with self.session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"]
                    subnets = result.get("subnets", [])
                    
                    if subnets:
                        pages = [subnets[i:i + 10] for i in range(0, len(subnets), 10)]
                        current_page = 0
                        embed = discord.Embed(title=f"Subnets for ASN#{asn}", color=0xFF6633)
                        embed.add_field(name="Subnets", value="\n".join([f"- {subnet}" for subnet in pages[current_page]]), inline=False)
                        message = await ctx.send(embed=embed)

                        if len(pages) > 1:
                            await message.add_reaction("◀️")
                            await message.add_reaction("❌")
                            await message.add_reaction("▶️")

                            def check(reaction, user):
                                return user == ctx.author and str(reaction.emoji) in ["◀️", "❌", "▶️"] and reaction.message.id == message.id

                            while True:
                                try:
                                    reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

                                    if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                                        current_page += 1
                                        embed.clear_fields()
                                        for subnet in pages[current_page]:
                                            embed.add_field(name="Subnet", value=f"**`{subnet}`**", inline=False)
                                        await message.edit(embed=embed)
                                        await message.remove_reaction(reaction, user)

                                    elif str(reaction.emoji) == "◀️" and current_page > 0:
                                        current_page -= 1
                                        embed.clear_fields()
                                        for subnet in pages[current_page]:
                                            embed.add_field(name="Subnet", value=f"**`{subnet}`**", inline=False)
                                        await message.edit(embed=embed)
                                        await message.remove_reaction(reaction, user)

                                    elif str(reaction.emoji) == "❌":
                                        await message.delete()
                                        break

                                except asyncio.TimeoutError:
                                    await message.clear_reactions()
                                    break
                    else:
                        embed = discord.Embed(title=f"Subnets for ASN#{asn}", color=0xFF6633)
                        embed.add_field(name="Subnets", value="No subnets found for this ASN.", inline=False)
                        await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Error", description=f"Error: {data['errors']}", color=0xff4545)
                    await ctx.send(embed=embed)
            elif response.status == 400:
                embed = discord.Embed(title="Bad Request", description="The server could not understand the request due to invalid syntax.", color=0xff4545)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Failed to query Cloudflare API", description=f"Status code: {response.status}", color=0xff4545)
                await ctx.send(embed=embed)
   
    @commands.group()
    async def urlscanner(self, ctx):
        """
        Use the Cloudflare API to scan websites for threats via Discord.

        Learn more at https://developers.cloudflare.com/radar/investigate/url-scanner/
        """

    @commands.admin_or_permissions() 
    @urlscanner.command(name="search")
    async def search_url_scan(self, ctx, query: str):
        """Search for URL scans by date and webpage requests."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")

        if not account_id or not bearer_token:
            embed = discord.Embed(
                title="Configuration Error",
                description="Missing account ID or bearer token. Please check your configuration.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan"
        params = {"query": query}

        try:
            async with self.session.get(url, headers=headers, params=params) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Search URL Scans",
                        description=f"**Error:** {error_message}",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                results = data.get("result", {}).get("tasks", [])
                if not results:
                    embed = discord.Embed(
                        title="No Results",
                        description="No URL scans found for the given query.",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                pages = []
                current_page = discord.Embed(
                    title="URL Scan Results",
                    description=f"Search results for query: **`{query}`**",
                    color=0xFF6633
                )
                total_size = len(current_page.description)
                for result in results:
                    field_value = (
                        f"**Country:** {result.get('country', 'Unknown')}\n"
                        f"**Success:** {result.get('success', False)}\n"
                        f"**Time:** {result.get('time', 'Unknown')}\n"
                        f"**UUID:** {result.get('uuid', 'Unknown')}\n"
                        f"**Visibility:** {result.get('visibility', 'Unknown')}"
                    )
                    field_name = result.get("url", "Unknown URL")
                    if len(field_name) > 256:
                        field_name = field_name[:253] + "..."
                    field_size = len(field_name) + len(field_value)
                    if len(current_page.fields) == 25 or (total_size + field_size) > 6000:
                        pages.append(current_page)
                        current_page = discord.Embed(
                            title="URL Scan Results",
                            description=f"Search results for query: **`{query}`** (cont.)",
                            color=0x2BBD8E
                        )
                        total_size = len(current_page.description)
                    current_page.add_field(
                        name=field_name,
                        value=field_value,
                        inline=False
                    )
                    total_size += field_size
                pages.append(current_page)

                message = await ctx.send(embed=pages[0])
                if len(pages) > 1:
                    await message.add_reaction("◀️")
                    await message.add_reaction("❌")
                    await message.add_reaction("▶️")

                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) in ["◀️", "❌", "▶️"] and reaction.message.id == message.id

                    current_page_index = 0
                    while True:
                        try:
                            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

                            if str(reaction.emoji) == "▶️" and current_page_index < len(pages) - 1:
                                current_page_index += 1
                                await message.edit(embed=pages[current_page_index])
                                await message.remove_reaction(reaction, user)

                            elif str(reaction.emoji) == "◀️" and current_page_index > 0:
                                current_page_index -= 1
                                await message.edit(embed=pages[current_page_index])
                                await message.remove_reaction(reaction, user)

                            elif str(reaction.emoji) == "❌":
                                await message.delete()
                                break

                        except asyncio.TimeoutError:
                            await message.clear_reactions()
                            break
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=0xff4545
            ))

    @urlscanner.command(name="create")
    async def scan_url(self, ctx, url: str):
        """Start a new scan for the provided URL."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")

        if not account_id or not bearer_token:
            embed = discord.Embed(
                title="Configuration Error",
                description="Missing account ID or bearer token. Please check your configuration.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "url": url
        }

        api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan"

        try:
            async with self.session.post(api_url, headers=headers, json=payload) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Start URL Scan",
                        description=f"**Error:** {error_message}",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                result = data.get("result", {})
                embed = discord.Embed(
                    title="URL Scan Started",
                    description=f"Scan started successfully.",
                    color=0xFF6633
                )
                embed.add_field(name="UUID", value=f"**`{result.get('uuid', 'Unknown')}`**", inline=True)
                embed.add_field(name="Visibility", value=f"**`{result.get('visibility', 'Unknown')}`**", inline=True)
                embed.add_field(name="Target", value=f"**`{url}`**", inline=True)
                time_value = result.get('time', 'Unknown')
                if time_value != 'Unknown':
                    from datetime import datetime
                    dt = datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                    time_value = f"<t:{int(dt.timestamp())}:F>"
                embed.add_field(name="Time", value=f"**`{time_value}`**", inline=True)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=0xff4545
            ))

    @urlscanner.command(name="results")
    async def get_scan_result(self, ctx, scan_id: str):
        """Get the result of a URL scan by its ID."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")

        if not all([account_id, bearer_token]):
            embed = discord.Embed(
                title="Configuration Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan/{scan_id}"

        try:
            async with self.session.get(api_url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Retrieve URL Scan Result",
                        description=f"**Error:** {error_message}",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                result = data.get("result", {}).get("scan", {})
                if not result:
                    await ctx.send(embed=discord.Embed(
                        title="No Data",
                        description="No relevant data found in the scan result.",
                        color=0xFF6633
                    ))
                    return

                task = result.get('task', {})
                verdicts = result.get('verdicts', {})
                meta = result.get('meta', {})
                processors = meta.get('processors', {})
                tech = processors.get('tech', [])
                task_url = task.get('url', 'Unknown')
                task_domain = task_url.split('/')[2] if task_url != 'Unknown' else 'Unknown'
                categories = []
                domains = result.get('domains', {})
                if task_domain in domains:
                    domain_data = domains[task_domain]
                    content_categories = domain_data.get('categories', {}).get('content', [])
                    inherited_categories = domain_data.get('categories', {}).get('inherited', {}).get('content', [])
                    categories.extend(content_categories + inherited_categories)

                embed = discord.Embed(
                    title="Scan results",
                    description=f"### Scan result for ID\n```{scan_id}```",
                    color=0x2BBD8E
                )
                embed.add_field(name="Target URL", value=f"```{task_url}```", inline=False)
                embed.add_field(name="Effective URL", value=f"```{task.get('effectiveUrl', 'Unknown')}```", inline=False)
                embed.add_field(name="Status", value=f"**`{task.get('status', 'Unknown')}`**", inline=True)
                embed.add_field(name="Visibility", value=f"**`{task.get('visibility', 'Unknown')}`**", inline=True)
                malicious_result = verdicts.get('overall', {}).get('malicious', 'Unknown')
                embed.add_field(name="Malicious", value=f"**`{malicious_result}`**", inline=True)
                embed.add_field(name="Tech", value=f"**`{', '.join([tech_item['name'] for tech_item in tech])}`**", inline=True)
                embed.add_field(name="Categories", value=f"**`{', '.join([category['name'] for category in categories])}`**", inline=True)
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=0xff4545
            ))

    @urlscanner.command(name="har")
    async def fetch_har(self, ctx, scan_id: str):
        """Fetch the HAR of a scan by the scan ID"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan/{scan_id}/har"

        try:
            async with self.session.get(api_url, headers=headers) as response:
                data = await response.json()
                if not data.get("success", False):
                    error_message = data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                    embed = discord.Embed(
                        title="Failed to Retrieve HAR",
                        description=f"**Error:** {error_message}",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                har_data = data.get("result", {}).get("har", {})
                if not har_data:
                    await ctx.send(embed=discord.Embed(
                        title="No Data",
                        description="No HAR data found for the given scan ID.",
                        color=0xff4545
                    ))
                    return

                # Send HAR data as a file
                har_json = json.dumps(har_data, indent=4)
                har_file = discord.File(io.StringIO(har_json), filename=f"{scan_id}_har.json")
                await ctx.send(file=har_file)

        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=0xff4545
            ))

    @urlscanner.command(name="screenshot")
    async def get_scan_screenshot(self, ctx, scan_id: str):
        """Get the screenshot of a scan by its scan ID"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        screenshot_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan/{scan_id}/screenshot"

        try:
            async with self.session.get(screenshot_url, headers=headers) as screenshot_response:
                if screenshot_response.content_type == "image/png":
                    screenshot_data = await screenshot_response.read()
                    screenshot_file = discord.File(io.BytesIO(screenshot_data), filename=f"{scan_id}_screenshot.png")
                    embed = discord.Embed(
                        title="Screenshot fetched from scan",
                        description=f"### Screenshot for scan ID\n```{scan_id}```",
                        color=0x2BBD8E
                    )
                    screenshot_size = len(screenshot_data)
                    embed.add_field(name="File Size", value=f"**`{screenshot_size} bytes`**", inline=True)

                    # Assuming the resolution can be derived from the image data
                    image = Image.open(io.BytesIO(screenshot_data))
                    resolution = f"**`{image.width}`x`{image.height}`**"
                    embed.add_field(name="Resolution", value=resolution, inline=True)
                    embed.set_image(url=f"attachment://{scan_id}_screenshot.png")
                    await ctx.send(embed=embed, file=screenshot_file)
                else:
                    screenshot_data = await screenshot_response.json()
                    if not screenshot_data.get("success", False):
                        error_message = screenshot_data.get("errors", [{"message": "Unknown error"}])[0].get("message")
                        embed = discord.Embed(
                            title="Failed to retrieve screenshot",
                            description=f"**`{error_message}`**",
                            color=0xff4545
                        )
                        await ctx.send(embed=embed)
                        return
        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=0xff4545
            ))

    @urlscanner.command(name="scan")
    async def scan_url(self, ctx, url: str):
        """Scan a URL using Cloudflare URL Scanner and return the verdict."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        # Submit the URL for scanning
        submit_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan"
        payload = {"url": url}

        try:
            async with self.session.post(submit_url, headers=headers, json=payload) as response:
                if response.status == 409:
                    embed = discord.Embed(title="Domain on cooldown", description="The domain was too recently scanned. Please try again in a few minutes.", color=0xff4545)
                    await ctx.send(embed=embed)
                    return
                elif response.status != 200:
                    embed = discord.Embed(title="Error", description=f"Failed to submit URL for scanning: {response.status}", color=0xff4545)
                    await ctx.send(embed=embed)
                    return

                data = await response.json()
                if not data.get("success", False):
                    embed = discord.Embed(title="Error", description="Failed to submit URL for scanning.", color=0xff4545)
                    await ctx.send(embed=embed)
                    return

                scan_id = data["result"]["uuid"]
                embed = discord.Embed(title="Cloudflare is scanning your URL", description=f"This scan may take a few moments to complete, please wait patiently.", color=0xFF6633)
                embed.set_footer(text=f"{scan_id}")
                await ctx.send(embed=embed)
                await ctx.typing()

        except Exception as e:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description=f"An error occurred while submitting the URL: {str(e)}",
                color=0xff4545
            ))
            return

        # Check the scan status every 10-15 seconds
        status_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan/{scan_id}"
        while True:
            await asyncio.sleep(15)
            try:
                async with self.session.get(status_url, headers=headers) as response:
                    if response.status == 202:
                        await ctx.typing()
                        continue
                    elif response.status != 200:
                        embed = discord.Embed(title="Error", description=f"Failed to check scan status: {response.status}", color=0xff4545)
                        await ctx.send(embed=embed)
                        return

                    data = await response.json()
                    if not data.get("success", False):
                        embed = discord.Embed(title="Error", description="Failed to check scan status.", color=0xff4545)
                        await ctx.send(embed=embed)
                        return

                    if response.status == 200:
                        scan_result = data["result"]["scan"]
                        verdict = scan_result["verdicts"]["overall"]
                        malicious = verdict["malicious"]
                        categories = ", ".join([cat["name"] for cat in verdict["categories"]])
                        phishing = ", ".join(verdict.get("phishing", []))

                        if malicious:
                            embed = discord.Embed(
                                title="Cloudflare detected a threat",
                                description=f"A URL scan has completed and Cloudflare has detected one or more threats",
                                color=0xff4545
                            )
                            embed.set_footer(text=f"{scan_id}")
                        else:
                            embed = discord.Embed(
                                title="Cloudflare detected no threats",
                                description=f"A URL scan has finished with no detections to report.",
                                color=0x2BBD8E
                            )
                            embed.set_footer(text=f"{scan_id}")

                        if categories:
                            embed.add_field(name="Categories", value=f"{categories}", inline=False)
                        if phishing:
                            embed.add_field(name="Phishing", value=f"{phishing}", inline=False)

                        # Add a URL button to view the report
                        view = discord.ui.View()
                        report_url = f"https://radar.cloudflare.com/scan/{scan_id}"
                        report_button = discord.ui.Button(label="View on Cloudflare Radar", url=report_url, style=discord.ButtonStyle.link)
                        view.add_item(report_button)
                        await ctx.send(embed=embed, view=view)
                        return

            except Exception as e:
                await ctx.send(embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while checking the scan status: {str(e)}",
                    color=0xff4545
                ))
                return

    @urlscanner.command(name="autoscan")
    @commands.has_permissions(administrator=True)
    async def set_autoscan(self, ctx: commands.Context, enabled: bool):
        """
        Enable or disable automatic URL scans.
        """
        await self.config.guild(ctx.guild).auto_scan.set(enabled)
        status = "enabled" if enabled else "disabled"
        embed = discord.Embed(
            title='Settings changed',
            description=f"Automatic URL scans utilizing Cloudflare threat intelligence have been **{status}**.",
            colour=0xffd966,
        )
        await ctx.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        # Check if the message.guild is None
        if message.guild is None:
            return

        # Check if autoscan is enabled
        auto_scan_enabled = await self.config.guild(message.guild).auto_scan()
        if not auto_scan_enabled:
            return

        urls = [word for word in message.content.split() if word.startswith("http://") or word.startswith("https://")]
        if not urls:
            return

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        account_id = api_tokens.get("account_id")
        bearer_token = api_tokens.get("bearer_token")

        if not account_id or not bearer_token:
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        for url in urls:
            payload = {"url": url}
            api_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan"

            try:
                async with self.session.post(api_url, headers=headers, json=payload) as response:
                    data = await response.json()
                    if not data.get("success", False):
                        continue

                    scan_id = data.get("result", {}).get("uuid")
                    if not scan_id:
                        continue

                    await asyncio.sleep(120)

                    scan_result_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/urlscanner/scan/{scan_id}"
                    async with self.session.get(scan_result_url, headers=headers) as scan_response:
                        scan_data = await scan_response.json()
                        if not scan_data.get("success", False):
                            continue

                        result = scan_data.get("result", {}).get("scan", {})
                        verdicts = result.get("verdicts", {})
                        malicious = verdicts.get("overall", {}).get("malicious", False)

                        if malicious:
                            await message.delete()
                            embed = discord.Embed(
                                title="Cloudflare detected a threat!",
                                description=f"Cloudflare detected a threat in a message sent in this channel and removed it to safeguard the community.",
                                color=0xFF6633
                            )
                            await message.channel.send(embed=embed)
                            return

            except Exception as e:
                await message.channel.send(embed=discord.Embed(
                    title="Error",
                    description=f"An error occurred while processing the URL scan: {str(e)}",
                    color=0xff4545
                ))





    @commands.is_owner()
    @commands.group(invoke_without_command=False)
    async def emailrouting(self, ctx):
        """Cloudflare Email Routing is designed to simplify the way you create and manage email addresses, without needing to keep an eye on additional mailboxes. Learn more at https://developers.cloudflare.com/email-routing/"""

    @commands.is_owner()
    @emailrouting.command(name="list")
    async def list_email_routing_addresses(self, ctx):
        """List current destination addresses"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        async with self.session.get(f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/routing/addresses", headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(title="Error", description=f"Failed to fetch Email Routing addresses: {response.status}", color=0xff4545)
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(title="Error", description="Failed to fetch Email Routing addresses.", color=0xff4545)
                await ctx.send(embed=embed)
                return

            addresses = data.get("result", [])
            if not addresses:
                embed = discord.Embed(title="Email Routing Addresses", description="No Email Routing addresses found.", color=0xff4545)
                await ctx.send(embed=embed)
                return

            pages = [addresses[i:i + 10] for i in range(0, len(addresses), 10)]
            current_page = 0

            embed = discord.Embed(title="Email Routing address list", description="\n".join([f"**`{addr['email']}`**" for addr in pages[current_page]]), color=0x2BBD8E)
            message = await ctx.send(embed=embed)

            if len(pages) > 1:
                await message.add_reaction("◀️")
                await message.add_reaction("❌")
                await message.add_reaction("▶️")

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in ["◀️", "❌", "▶️"] and reaction.message.id == message.id

                while True:
                    try:
                        reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)

                        if str(reaction.emoji) == "▶️" and current_page < len(pages) - 1:
                            current_page += 1
                            embed.description = "\n".join([f"**`{addr['email']}`**" for addr in pages[current_page]])
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "◀️" and current_page > 0:
                            current_page -= 1
                            embed.description = "\n".join([f"**`{addr['email']}`**" for addr in pages[current_page]])
                            await message.edit(embed=embed)
                            await message.remove_reaction(reaction, user)

                        elif str(reaction.emoji) == "❌":
                            await message.delete()
                            break

                    except asyncio.TimeoutError:
                        await message.clear_reactions()
                        break

    @commands.is_owner()
    @emailrouting.command(name="add")
    async def create_email_routing_address(self, ctx, email: str):
        """Add a new destination address to your Email Routing service."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email_token = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email_token, api_key, bearer_token, account_id]):
            embed = discord.Embed(title="Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/routing/addresses"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email_token,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "email": email
        }

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                if data["success"]:
                    result = data["result"]
                    embed = discord.Embed(title="Destination address added", description="You or the owner of this inbox will need to click the link they were sent just now to enable their email as a destination within your Cloudflare account", color=0x2BBD8E)
                    embed.add_field(name="Email", value=f"**`{result['email']}`**", inline=False)
                    embed.add_field(name="ID", value=f"**`{result['id']}`**", inline=False)
                    embed.add_field(name="Created", value=f"**`{result['created']}`**", inline=False)
                    embed.add_field(name="Modified", value=f"**`{result['modified']}`**", inline=False)
                    embed.add_field(name="Verified", value=f"**`{result['verified']}`**", inline=False)
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(title="Error", description=f"Error: {data['errors']}", color=0xff4545)
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title="Error", description=f"Failed to create email routing address. Status code: {response.status}", color=0xff4545)
                await ctx.send(embed=embed)

    @commands.is_owner()
    @emailrouting.command(name="remove")
    async def remove_email_routing_address(self, ctx, email: str):
        """Remove a destination address from your Email Routing service."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email_token = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email_token, api_key, bearer_token, account_id]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        # Query to get the ID of the address to be deleted
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/routing/addresses"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email_token,
            "X-Auth-Key": api_key,
            "Content-Type": "application/json",
        }

        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch email routing addresses. Status code: {response.status}",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to fetch email routing addresses.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return

            addresses = data.get("result", [])
            address_id = None
            for address in addresses:
                if address["email"] == email:
                    address_id = address["id"]
                    break

            if not address_id:
                embed = discord.Embed(
                    title="Error",
                    description=f"No email routing address found for **`{email}`**.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return

        # Ask for confirmation
        embed = discord.Embed(
            title="Confirm destructive action",
            description=f"**Are you sure you want to remove this email routing address**\n**`{email}`**",
            color=0xff4545
        )
        embed.set_footer(text="React to confirm or cancel this request")
        confirmation_message = await ctx.send(embed=embed)
        await confirmation_message.add_reaction("✅")
        await confirmation_message.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirmation_message.id

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            if str(reaction.emoji) == "❌":
                embed = discord.Embed(
                    title="Cancelled",
                    description="Email routing address removal cancelled.",
                    color=0xff4545
                )
                await ctx.send(embed=embed)
                return
            elif str(reaction.emoji) == "✅":
                # Delete the address
                await asyncio.sleep(5)  # Wait for 5 seconds to avoid rate limiting
                delete_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/email/routing/addresses/{address_id}"
                async with self.session.delete(delete_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data["success"]:
                            embed = discord.Embed(
                                title="Destination address removed",
                                description=f"**Successfully removed email routing address**\n**`{email}`**",
                                color=0x2BBD8E
                            )
                            await ctx.send(embed=embed)
                        else:
                            embed = discord.Embed(
                                title="Error",
                                description=f"**Error:** {data['errors']}",
                                color=0xff4545
                            )
                            await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            title="Error",
                            description=f"Failed to remove email routing address. Status code: {response.status}",
                            color=0xff4545
                        )
                        await ctx.send(embed=embed)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout",
                description="Confirmation timed out. Email routing address removal cancelled.",
                color=0xff4545
            )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @emailrouting.command(name="settings")
    async def get_email_routing_settings(self, ctx):
        """Get and display the current Email Routing settings for a specific zone"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, account_id, zone_identifier]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=0xff4545  # Red color for error
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing"
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch Email Routing settings: {response.status}",
                    color=0xff4545  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to fetch Email Routing settings.",
                    color=0xff4545  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            settings = data.get("result", {})
            if not settings:
                embed = discord.Embed(
                    title="Error",
                    description="No Email Routing settings found.",
                    color=0xff4545  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="Current settings for Email Routing",
                description=f"**Settings for zone `{zone_identifier.upper()}`**\n\n*Change your zone using `[p]set api cloudflare zone_id`*",
                color=0x2BBD8E  # Green color for success
            )
            created_timestamp = settings.get('created', 'N/A')
            if created_timestamp != 'N/A':
                created_timestamp = f"<t:{int(datetime.fromisoformat(created_timestamp).timestamp())}:F>"
            embed.add_field(name="Created", value=f"**{created_timestamp}**", inline=False)
            embed.add_field(name="Enabled", value=f"**`{settings.get('enabled', 'N/A')}`**", inline=False)
            embed.add_field(name="ID", value=f"**`{settings.get('id', 'N/A').upper()}`**", inline=False)
            modified_timestamp = settings.get('modified', 'N/A')
            if modified_timestamp != 'N/A':
                modified_timestamp = f"<t:{int(datetime.fromisoformat(modified_timestamp).timestamp())}:F>"
            embed.add_field(name="Modified", value=f"**{modified_timestamp}**", inline=False)
            embed.add_field(name="Name", value=f"**`{settings.get('name', 'N/A')}`**", inline=False)
            embed.add_field(name="Skipped wizard", value=f"**`{str(settings.get('skip_wizard', 'N/A')).upper()}`**", inline=False)
            embed.add_field(name="Status", value=f"**`{str(settings.get('status', 'N/A')).upper()}`**", inline=False)
            embed.add_field(name="Synced", value=f"**`{str(settings.get('synced', 'N/A')).upper()}`**", inline=False)
            embed.add_field(name="Tag", value=f"**`{str(settings.get('tag', 'N/A')).upper()}`**", inline=False)

            await ctx.send(embed=embed)
    
    @commands.is_owner()
    @emailrouting.command(name="enable")
    async def enable_email_routing(self, ctx):
        """Enable Email Routing for the selected zone"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=0xff4545  # Red color for error
            )
            await ctx.send(embed=embed)
            return

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        embed = discord.Embed(
            title="Enable Email Routing",
            description=(
                "Enabling Email Routing will allow Cloudflare to proxy your emails for the selected zone. "
                "This might affect how your emails are delivered. Type `yes` to confirm or `no` to cancel."
            ),
            color=0xff9144  # Default color
        )
        await ctx.send(embed=embed)

        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Error",
                description="Confirmation timed out. Email Routing enable operation cancelled.",
                color=0xff4545  # Red color for error
            )
            await ctx.send(embed=embed)
            return

        if confirmation.content.lower() != 'yes':
            embed = discord.Embed(
                title="Cancelled",
                description="Email Routing enable operation cancelled.",
                color=0xff9144  # Default color for cancellation
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/enable"
        async with self.session.post(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to enable Email Routing: {response.status}",
                    color=0xff4545  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to enable Email Routing.",
                    color=0xff4545  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="Success",
                description=f"Email Routing has been successfully enabled for zone `{zone_identifier.upper()}`.",
                color=0x2BBD8E  # Green color for success
            )
            await ctx.send(embed=embed)
    
    @commands.is_owner()
    @emailrouting.command(name="disable")
    async def disable_email_routing(self, ctx):
        """Disable Email Routing for the selected zone"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=0xff4545  # Red color for error
            )
            await ctx.send(embed=embed)
            return

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        await ctx.send(
            "Are you sure you want to disable Email Routing? This will stop emails from being proxied by Cloudflare, "
            "and you might miss critical communications. Type `yes` to confirm or `no` to cancel."
        )

        try:
            confirmation = await self.bot.wait_for('message', check=check, timeout=30.0)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title="Timeout",
                description="Confirmation timed out. Email Routing disable operation cancelled.",
                color=0xff4545  # Red color for error
            )
            await ctx.send(embed=embed)
            return

        if confirmation.content.lower() != 'yes':
            embed = discord.Embed(
                title="Cancelled",
                description="Email Routing disable operation cancelled.",
                color=0xff9144  # Default color for cancellation
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/disable"
        async with self.session.post(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to disable Email Routing: {response.status}",
                    color=0xff4545  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to disable Email Routing.",
                    color=0xff4545  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="Success",
                description=f"Email Routing has been successfully disabled for zone `{zone_identifier.upper()}`.",
                color=0x2BBD8E  # Green color for success
            )
            await ctx.send(embed=embed)
    
    @commands.is_owner()
    @emailrouting.command(name="records")
    async def get_email_routing_dns_records(self, ctx):
        """Get the required DNS records to setup Email Routing"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")  # Red color for error
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/dns"
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch DNS records for Email Routing: {response.status}",
                    color=discord.Color.from_str("#ff4545")  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to fetch DNS records for Email Routing.",
                    color=discord.Color.from_str("#ff4545")  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            records = data.get("result", [])
            if not records:
                embed = discord.Embed(
                    title="No Records",
                    description="No DNS records found for Email Routing.",
                    color=discord.Color.from_str("#ff4545")  # Red color for error
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(title="Email Routing DNS Records", color=discord.Color.from_str("#2BBD8E"))  # Green color for success
            for record in records:
                embed.add_field(
                    name=f"{record['type']} Record",
                    value=f"**Name:** {record['name']}\n**Content:** {record['content']}\n**Priority:** {record.get('priority', 'N/A')}\n**TTL:** {record['ttl']}",
                    inline=False
                )

            await ctx.send(embed=embed)
    
    @commands.is_owner()
    @emailrouting.group(name="rules", invoke_without_command=True)
    async def email_routing_rules(self, ctx):
        """Manage your Email Routing rules"""
        await ctx.send_help(ctx.command)

    @commands.is_owner()
    @email_routing_rules.command(name="add")
    async def add_email_routing_rule(self, ctx, source: str, destination: str):
        """Add a rule to Email Routing"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")  # Error color
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/rules"
        payload = {
            "source": source,
            "destination": destination
        }

        async with self.session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to add Email Routing rule: {response.status}",
                    color=discord.Color.from_str("#ff4545")  # Error color
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to add Email Routing rule.",
                    color=discord.Color.from_str("#ff4545")  # Error color
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="Success",
                description=f"Email Routing rule added successfully: {source} -> {destination}",
                color=discord.Color.from_str("#2BBD8E")  # Success color
            )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @email_routing_rules.command(name="remove")
    async def remove_email_routing_rule(self, ctx, rule_id: str):
        """Remove a rule from Email Routing"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")  # Error color
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/rules/{rule_id}"

        async with self.session.delete(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to remove Email Routing rule: {response.status}",
                    color=discord.Color.from_str("#ff4545")  # Error color
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to remove Email Routing rule.",
                    color=discord.Color.from_str("#ff4545")  # Error color
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="Success",
                description=f"Email Routing rule removed successfully: {rule_id}",
                color=discord.Color.from_str("#2BBD8E")  # Success color
            )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @email_routing_rules.command(name="list")
    async def list_email_routing_rules(self, ctx):
        """Show current Email Routing rules"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        zone_identifier = api_tokens.get("zone_id")

        if not all([email, api_key, bearer_token, zone_identifier]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")  # Error color
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_identifier}/email/routing/rules"

        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch Email Routing rules: {response.status}",
                    color=discord.Color.from_str("#ff4545")  # Error color
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to fetch Email Routing rules.",
                    color=discord.Color.from_str("#ff4545")  # Error color
                )
                await ctx.send(embed=embed)
                return

            rules = data.get("result", [])
            if not rules:
                embed = discord.Embed(
                    title="Error",
                    description="No Email Routing rules found.",
                    color=discord.Color.from_str("#ff4545")  # Error color
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(title="Email Routing Rules", color=discord.Color.from_str("#2BBD8E"))  # Success color
            for rule in rules:
                actions = ", ".join([action["type"] for action in rule["actions"]])
                destinations = ", ".join([value if isinstance(value, str) else str(value) for action in rule["actions"] for value in (action.get("value", []) if isinstance(action.get("value", []), list) else [action.get("value", [])])])
                matchers = ", ".join([f"{matcher.get('field', 'unknown')}: {matcher.get('value', 'unknown')}" for matcher in rule["matchers"]])
                embed.add_field(
                    name=f"Rule ID: {rule['id']}",
                    value=f"**Name:** {rule['name']}\n**Enabled:** {rule['enabled']}\n**Actions:** {actions}\n**Destinations:** {destinations}\n**Matchers:** {matchers}\n**Priority:** {rule['priority']}\n**Tag:** {rule['tag']}",
                    inline=False
                )

            await ctx.send(embed=embed)
    

    @commands.is_owner()
    @commands.group(invoke_without_command=False)
    async def hyperdrive(self, ctx):
        """Hyperdrive is a service that accelerates queries you make to existing databases, making it faster to access your data from across the globe, irrespective of your users’ location. Learn more at https://developers.cloudflare.com/hyperdrive/"""
            
    @commands.is_owner()
    @hyperdrive.command(name="list")
    async def list_hyperdrives(self, ctx):
        """List current Hyperdrives in the specified account"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        email = api_tokens.get("email")
        api_key = api_tokens.get("api_key")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([email, api_key, bearer_token, account_id]):
            embed = discord.Embed(
                title="Authentication error",
                description="Your bot is missing one or more authentication elements required to interact with your Cloudflare account securely. Please ensure you have set an `api_key`, `email`, `bearer_token`, and `account_id` for this command to function properly. If you're not sure what this error means, ask your systems admin, or a more tech-inclined friend.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json"
        }

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs"

        async with self.session.get(url, headers=headers) as response:
            if response.status == 401:
                embed = discord.Embed(
                    title="Upgrade required",
                    description="**Cloudflare Hyperdrive** requires the attached **Cloudflare account** to be subscribed to a **Workers Paid** plan.",
                    color=discord.Color.from_str("#ff4545")
                )
                button = discord.ui.Button(
                    label="Hyperdrive prerequisites",
                    url="https://developers.cloudflare.com/hyperdrive/get-started/#prerequisites"
                )
                button2 = discord.ui.Button(
                    label="Workers pricing",
                    url="https://developers.cloudflare.com/workers/platform/pricing/#workers"
                )
                view = discord.ui.View()
                view.add_item(button)
                view.add_item(button2)
                await ctx.send(embed=embed, view=view)
                return
            elif response.status != 200:
                await ctx.send(f"Failed to fetch Hyperdrives: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to fetch Hyperdrives.")
                return

            hyperdrives = data.get("result", [])
            if not hyperdrives:
                await ctx.send("No Hyperdrives found.")
                return

            embed = discord.Embed(title="Hyperdrives", color=discord.Color.from_str("#2BBD8E"))
            for hyperdrive in hyperdrives:
                caching = hyperdrive["caching"]
                origin = hyperdrive["origin"]
                embed.add_field(
                    name=f"Hyperdrive ID: {hyperdrive['id']}",
                    value=(
                        f"**Name:** {hyperdrive['name']}\n"
                        f"**Caching Disabled:** {caching['disabled']}\n"
                        f"**Max Age:** {caching['max_age']} seconds\n"
                        f"**Stale While Revalidate:** {caching['stale_while_revalidate']} seconds\n"
                        f"**Origin Database:** {origin['database']}\n"
                        f"**Origin Host:** {origin['host']}\n"
                        f"**Origin Port:** {origin['port']}\n"
                        f"**Origin Scheme:** {origin['scheme']}\n"
                        f"**Origin User:** {origin['user']}"
                    ),
                    inline=False
                )

            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="create")
    async def create_hyperdrive(self, ctx, name: str, password: str, database: str, host: str, port: str, scheme: str, user: str, caching_disabled: bool, max_age: int, stale_while_revalidate: int):
        """Create a new Hyperdrive"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")

        if not all([email, api_key, bearer_token, account_id]):
            await ctx.send("Bearer token or account ID not set.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs"
        payload = {
            "origin": {
                "password": password,
                "database": database,
                "host": host,
                "port": port,
                "scheme": scheme,
                "user": user
            },
            "caching": {
                "disabled": caching_disabled,
                "max_age": max_age,
                "stale_while_revalidate": stale_while_revalidate
            },
            "name": name
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        async with self.session.post(url, json=payload, headers=headers) as response:
            if response.status == 401:
                embed = discord.Embed(
                    title="Upgrade required",
                    description="**Cloudflare Hyperdrive** requires the attached **Cloudflare account** to be subscribed to a **Workers Paid** plan.",
                    color=discord.Color.from_str("#ff4545")
                )
                button = discord.ui.Button(
                    label="Hyperdrive prerequisites",
                    url="https://developers.cloudflare.com/hyperdrive/get-started/#prerequisites"
                )
                button2 = discord.ui.Button(
                    label="Workers pricing",
                    url="https://developers.cloudflare.com/workers/platform/pricing/#workers"
                )
                view = discord.ui.View()
                view.add_item(button)
                view.add_item(button2)
                await ctx.send(embed=embed, view=view)
                return
            elif response.status != 200:
                await ctx.send(f"Failed to create Hyperdrive: {response.status}")
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send("Failed to create Hyperdrive.")
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Hyperdrive successfully created", color=discord.Color.from_str("#2BBD8E"))
            embed.add_field(name="ID", value=result.get("id"), inline=False)
            embed.add_field(name="Name", value=result.get("name"), inline=False)
            embed.add_field(name="Database", value=result["origin"].get("database"), inline=False)
            embed.add_field(name="Host", value=result["origin"].get("host"), inline=False)
            embed.add_field(name="Port", value=result["origin"].get("port"), inline=False)
            embed.add_field(name="Scheme", value=result["origin"].get("scheme"), inline=False)
            embed.add_field(name="User", value=result["origin"].get("user"), inline=False)
            embed.add_field(name="Caching Disabled", value=result["caching"].get("disabled"), inline=False)
            embed.add_field(name="Max Age", value=result["caching"].get("max_age"), inline=False)
            embed.add_field(name="Stale While Revalidate", value=result["caching"].get("stale_while_revalidate"), inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="delete")
    async def delete_hyperdrive(self, ctx, hyperdrive_id: str):
        """Delete a Hyperdrive."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs/{hyperdrive_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        async with self.session.delete(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to delete Hyperdrive: {response.status}",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to delete Hyperdrive.",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="Success",
                description=f"Hyperdrive {hyperdrive_id} successfully deleted.",
                color=discord.Color.from_str("#2BBD8E")
            )
            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="info")
    async def get_hyperdrive_info(self, ctx, hyperdrive_id: str):
        """Fetch information about a specified Hyperdrive by its ID."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            embed = discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")
            )
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs/{hyperdrive_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="Error",
                    description=f"Failed to fetch Hyperdrive info: {response.status}",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data.get("success", False):
                embed = discord.Embed(
                    title="Error",
                    description="Failed to fetch Hyperdrive info.",
                    color=discord.Color.from_str("#ff4545")
                )
                await ctx.send(embed=embed)
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Hyperdrive Information", color=discord.Color.from_str("#2BBD8E"))
            embed.add_field(name="ID", value=result.get("id"), inline=False)
            embed.add_field(name="Name", value=result.get("name"), inline=False)
            embed.add_field(name="Database", value=result["origin"].get("database"), inline=False)
            embed.add_field(name="Host", value=result["origin"].get("host"), inline=False)
            embed.add_field(name="Port", value=result["origin"].get("port"), inline=False)
            embed.add_field(name="Scheme", value=result["origin"].get("scheme"), inline=False)
            embed.add_field(name="User", value=result["origin"].get("user"), inline=False)
            embed.add_field(name="Caching Disabled", value=result["caching"].get("disabled"), inline=False)
            embed.add_field(name="Max Age", value=result["caching"].get("max_age"), inline=False)
            embed.add_field(name="Stale While Revalidate", value=result["caching"].get("stale_while_revalidate"), inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="patch")
    async def patch_hyperdrive(self, ctx, hyperdrive_id: str, *, changes: str):
        """Patch a specified Hyperdrive by its ID with provided changes."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs/{hyperdrive_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            changes_dict = json.loads(changes)
        except json.JSONDecodeError:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Invalid JSON format for changes.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        async with self.session.patch(url, headers=headers, json=changes_dict) as response:
            if response.status != 200:
                await ctx.send(embed=discord.Embed(
                    title="Error",
                    description=f"Failed to patch Hyperdrive: {response.status}",
                    color=discord.Color.from_str("#ff4545")
                ))
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send(embed=discord.Embed(
                    title="Error",
                    description="Failed to patch Hyperdrive.",
                    color=discord.Color.from_str("#ff4545")
                ))
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Patched Hyperdrive Information", color=discord.Color.from_str("#2BBD8E"))
            embed.add_field(name="ID", value=result.get("id"), inline=False)
            embed.add_field(name="Name", value=result.get("name"), inline=False)
            embed.add_field(name="Database", value=result["origin"].get("database"), inline=False)
            embed.add_field(name="Host", value=result["origin"].get("host"), inline=False)
            embed.add_field(name="Port", value=result["origin"].get("port"), inline=False)
            embed.add_field(name="Scheme", value=result["origin"].get("scheme"), inline=False)
            embed.add_field(name="User", value=result["origin"].get("user"), inline=False)
            embed.add_field(name="Caching Disabled", value=result["caching"].get("disabled"), inline=False)
            embed.add_field(name="Max Age", value=result["caching"].get("max_age"), inline=False)
            embed.add_field(name="Stale While Revalidate", value=result["caching"].get("stale_while_revalidate"), inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @hyperdrive.command(name="update")
    async def update_hyperdrive(self, ctx, hyperdrive_id: str, changes: str):
        """Update and return the specified Hyperdrive configuration."""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/hyperdrive/configs/{hyperdrive_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            changes_dict = json.loads(changes)
        except json.JSONDecodeError:
            await ctx.send(embed=discord.Embed(
                title="Error",
                description="Invalid JSON format for changes.",
                color=discord.Color.from_str("#ff4545")
            ))
            return

        async with self.session.put(url, headers=headers, json=changes_dict) as response:
            if response.status != 200:
                await ctx.send(embed=discord.Embed(
                    title="Error",
                    description=f"Failed to update Hyperdrive: {response.status}",
                    color=discord.Color.from_str("#ff4545")
                ))
                return

            data = await response.json()
            if not data.get("success", False):
                await ctx.send(embed=discord.Embed(
                    title="Error",
                    description="Failed to update Hyperdrive.",
                    color=discord.Color.from_str("#ff4545")
                ))
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Updated Hyperdrive Information", color=discord.Color.from_str("#2BBD8E"))
            embed.add_field(name="ID", value=result.get("id"), inline=False)
            embed.add_field(name="Name", value=result.get("name"), inline=False)
            embed.add_field(name="Database", value=result["origin"].get("database"), inline=False)
            embed.add_field(name="Host", value=result["origin"].get("host"), inline=False)
            embed.add_field(name="Port", value=result["origin"].get("port"), inline=False)
            embed.add_field(name="Scheme", value=result["origin"].get("scheme"), inline=False)
            embed.add_field(name="User", value=result["origin"].get("user"), inline=False)
            embed.add_field(name="Caching Disabled", value=result["caching"].get("disabled"), inline=False)
            embed.add_field(name="Max Age", value=result["caching"].get("max_age"), inline=False)
            embed.add_field(name="Stale While Revalidate", value=result["caching"].get("stale_while_revalidate"), inline=False)

            await ctx.send(embed=embed)


    @commands.is_owner()
    @commands.group(invoke_without_command=False)
    async def r2(self, ctx):
        """Cloudflare R2 Storage allows developers to store large amounts of unstructured data without the costly egress bandwidth fees associated with typical cloud storage services. 
        
        Learn more at https://developers.cloudflare.com/r2/
        """

    @commands.is_owner()
    @r2.command(name="create")
    async def createbucket(self, ctx, name: str, location_hint: str):
        """Create a new R2 bucket
        
        **Valid location hints**

        **`apac`** - Asia-Pacific
        **`eeur`** - Eastern Europe
        **`enam`** - Eastern North America
        **`weur`** - Western Europe
        **`wnam`** - Western North America
        
        """
        valid_location_hints = {
            "apac": "Asia-Pacific",
            "eeur": "Eastern Europe",
            "enam": "Eastern North America",
            "weur": "Western Europe",
            "wnam": "Western North America"
        }
        
        if location_hint not in valid_location_hints:
            embed = discord.Embed(title="Invalid Location Hint", color=discord.Color.from_str("#ff4545"))
            embed.add_field(name="Error", value=f"'{location_hint}' is not a valid location hint.", inline=False)
            embed.add_field(name="Valid Location Hints", value="\n".join([f"**`{key}`** for **{value}**" for key, value in valid_location_hints.items()]), inline=False)
            await ctx.send(embed=embed)
            return

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }
        payload = {
            "name": name,
            "locationHint": location_hint
        }

        async with self.session.post(url, headers=headers, json=payload) as response:
            data = await response.json()
            if response.status != 200 or not data.get("success", False):
                errors = data.get("errors", [])
                error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                await ctx.send(embed=discord.Embed(
                    title="Error",
                    description=f"Failed to create bucket: {error_messages}",
                    color=discord.Color.from_str("#ff4545")
                ))
                return

            result = data.get("result", {})
            embed = discord.Embed(title="Bucket Created", color=discord.Color.from_str("#2BBD8E"))
            embed.add_field(name="Name", value=f"**`{result.get('name')}`**", inline=False)
            embed.add_field(name="Location", value=f"**`{result.get('location')}`**", inline=False)
            embed.add_field(name="Creation Date", value=f"**`{result.get('creation_date')}`**", inline=False)

            await ctx.send(embed=embed)

    @commands.is_owner()
    @r2.command(name="delete")
    async def deletebucket(self, ctx, bucket_name: str):
        """Delete a specified R2 bucket"""
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

        embed = discord.Embed(
            title="Confirm R2 bucket deletion",
            description=f"Are you sure you want to delete the bucket **`{bucket_name}`**?\n\n:warning: **This action cannot be undone**.",
            color=discord.Color.orange()
        )
        embed.set_footer(text="React with ✅ to confirm or ❌ to cancel.")
        confirmation_message = await ctx.send(embed=embed)
        await confirmation_message.add_reaction("✅")
        await confirmation_message.add_reaction("❌")

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Bucket deletion cancelled due to timeout.")
            return

        if str(reaction.emoji) == "❌":
            await ctx.send("Bucket deletion cancelled.")
            return

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            await ctx.send("Missing one or more required API tokens. Please check your configuration.")
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        async with self.session.delete(url, headers=headers) as response:
            data = await response.json()
            if response.status != 200 or not data.get("success", False):
                errors = data.get("errors", [])
                error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                embed = discord.Embed(title="Bucket deletion failed", color=discord.Color.from_str("#ff4545"))
                embed.add_field(name="Errors", value=f"**`{error_messages}`**", inline=False)
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(title="Bucket deleted successfully", color=discord.Color.from_str("#2BBD8E"))
            embed.add_field(name="Bucket", value=f"**`{bucket_name}`**", inline=False)
            await ctx.send(embed=embed)

    @commands.is_owner()
    @r2.command(name="info")
    async def getbucket(self, ctx, bucket_name: str):
        """Get info about an R2 bucket"""

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                data = await response.json()
                if response.status != 200 or not data.get("success", False):
                    errors = data.get("errors", [])
                    error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                    embed = discord.Embed(title="Failed to fetch bucket info", color=0xff4545)
                    embed.add_field(name="Errors", value=f"**`{error_messages}`**", inline=False)
                    await ctx.send(embed=embed)
                    return

                bucket_info = data.get("result", {})
                if not bucket_info:
                    embed = discord.Embed(title="No Information Found", description="No information found for the specified bucket.", color=0xff4545)
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(title="Bucket Information", color=discord.Color.from_str("#2BBD8E"))
                # Customize individual fields
                if "name" in bucket_info:
                    embed.add_field(name="Name", value=f"**`{bucket_info['name']}`**", inline=False)
                if "creation_date" in bucket_info:
                    embed.add_field(name="Creation Date", value=f"**`{bucket_info['creation_date']}`**", inline=False)
                if "location" in bucket_info:
                    embed.add_field(name="Location", value=f"**`{bucket_info['location'].upper()}`**", inline=False)
                if "storage_class" in bucket_info:
                    embed.add_field(name="Storage Class", value=f"**`{bucket_info['storage_class']}`**", inline=False)
                
                await ctx.send(embed=embed)
        except RuntimeError as e:
            embed = discord.Embed(title="Runtime Error", description=f"An error occurred: {str(e)}", color=0xff4545)
            await ctx.send(embed=embed)
            return
        
    @commands.is_owner()
    @r2.command(name="stash", help="Upload a file to the specified R2 bucket")
    async def upload_to_bucket(self, ctx, bucket_name: str):
        if not ctx.message.attachments:
            embed = discord.Embed(title="Upload Error", description="Please attach a file to upload.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        attachment = ctx.message.attachments[0]

        # Check file size (300 MB = 300 * 1024 * 1024 bytes)
        max_size = 300 * 1024 * 1024
        if attachment.size > max_size:
            embed = discord.Embed(title="Upload Error", description="File size exceeds the 300 MB limit.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        file_content = await attachment.read()

        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            embed = discord.Embed(title="Configuration Error", description="Missing one or more required API tokens. Please check your configuration.", color=0xff4545)
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects/{attachment.filename}"
        headers = {
            "Content-Type": "application/octet-stream",
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            start_time = time.monotonic()
            async with self.session.put(url, headers=headers, data=file_content) as response:
                end_time = time.monotonic()
                data = await response.json()
                if response.status != 200 or not data.get("success", False):
                    errors = data.get("errors", [])
                    error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                    embed = discord.Embed(title="Failed to upload file", color=0xff4545)
                    embed.add_field(name="Errors", value=f"**`{error_messages}`**", inline=False)
                    await ctx.send(embed=embed)
                    return

                upload_time = end_time - start_time
                embed = discord.Embed(title="File Uploaded Successfully", color=discord.Color.from_str("#2BBD8E"))
                embed.add_field(name="File Name", value=f"**`{attachment.filename}`**", inline=False)
                embed.add_field(name="Bucket Name", value=f"**`{bucket_name}`**", inline=False)
                def format_file_size(size):
                    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
                        if size < 1024.0:
                            return f"**`{size:.2f} {unit}`**"
                        size /= 1024.0
                    return f"**`{size:.2f} PB`**"  # In case the file is extremely large

                embed.add_field(name="File Size", value=format_file_size(attachment.size), inline=False)
                embed.add_field(name="Upload Time", value=f"**`{upload_time:.2f} seconds`**", inline=False)
                await ctx.send(embed=embed)
        except RuntimeError as e:
            embed = discord.Embed(title="Runtime Error", description=f"An error occurred: {str(e)}", color=0xff4545)
            await ctx.send(embed=embed)
            return
        
    @commands.is_owner()
    @r2.command(name="recycle")
    async def delete_file(self, ctx, bucket_name: str, file_name: str):
        """Delete a file by name from an R2 bucket"""
        api_tokens = await self.bot.get_shared_api_tokens("cloudflare")
        api_key = api_tokens.get("api_key")
        email = api_tokens.get("email")
        bearer_token = api_tokens.get("bearer_token")
        account_id = api_tokens.get("account_id")

        if not all([api_key, email, bearer_token, account_id]):
            embed = discord.Embed(
                title="Configuration Error",
                description="Missing one or more required API tokens. Please check your configuration.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        file_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects/{file_name}"
        try:
            async with self.session.delete(file_url, headers=headers) as delete_response:
                delete_data = await delete_response.json()
                if delete_response.status != 200 or not delete_data.get("success", False):
                    delete_error_messages = "\n".join([error.get("message", "Unknown error") for error in delete_data.get("errors", [])])
                    embed = discord.Embed(
                        title="Failed to delete file",
                        color=0xff4545
                    )
                    embed.add_field(
                        name="Errors",
                        value=f"**`{delete_error_messages}`**",
                        inline=False
                    )
                    await ctx.send(embed=embed)
                    return

                embed = discord.Embed(
                    title="File deleted from bucket",
                    color=discord.Color.from_str("#2BBD8E")
                )
                embed.add_field(
                    name="File name",
                    value=f"**`{file_name}`**",
                    inline=False
                )
                embed.add_field(
                    name="Bucket targeted",
                    value=f"**`{bucket_name}`**",
                    inline=False
                )
                await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An unexpected error occurred while deleting the file: {str(e)}",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
        

    @commands.is_owner()
    @r2.command(name="fetch")
    async def fetch_file(self, ctx, bucket_name: str, file_name: str):
        """Fetch a file from an R2 bucket"""
        api_info = await self.bot.get_shared_api_tokens("cloudflare")
        bearer_token = api_info.get("bearer_token")
        email = api_info.get("email")
        api_key = api_info.get("api_key")
        account_id = api_info.get("account_id")
        if not all([bearer_token, email, api_key, account_id]):
            embed = discord.Embed(
                title="API Key Error",
                description="Missing API keys. Please set them using the appropriate command.",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return

        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects/{file_name}"
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "X-Auth-Email": email,
            "X-Auth-Key": api_key,
        }

        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 413:
                    embed = discord.Embed(
                        title="Error",
                        description="413 Payload Too Large (error code: 40005): Request entity too large",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                if response.status != 200:
                    data = await response.json()
                    errors = data.get("errors", [])
                    error_messages = "\n".join([error.get("message", "Unknown error") for error in errors])
                    embed = discord.Embed(
                        title="Failed to fetch file by name",
                        color=0xff4545
                    )
                    embed.add_field(
                        name="Errors",
                        value=f"**`{error_messages}`**",
                        inline=False
                    )
                    await ctx.send(embed=embed)

                    # Additional logic to fetch by other attributes
                    list_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/r2/buckets/{bucket_name}/objects"
                    async with self.session.get(list_url, headers=headers) as list_response:
                        if list_response.status == 413:
                            embed = discord.Embed(
                                title="Error",
                                description="413 Payload Too Large (error code: 40005): Request entity too large",
                                color=0xff4545
                            )
                            await ctx.send(embed=embed)
                            return

                        if list_response.status != 200:
                            list_data = await list_response.json()
                            list_errors = list_data.get("errors", [])
                            list_error_messages = "\n".join([error.get("message", "Unknown error") for error in list_errors])
                            embed = discord.Embed(
                                title="Failed to list files in bucket",
                                color=0xff4545
                            )
                            embed.add_field(
                                name="Errors",
                                value=f"**`{list_error_messages}`**",
                                inline=False
                            )
                            await ctx.send(embed=embed)
                            return

                        list_data = await list_response.json()
                        objects = list_data.get("result", {}).get("objects", [])
                        for obj in objects:
                            if obj.get("name") == file_name:
                                file_url = obj.get("url")
                                async with self.session.get(file_url, headers=headers) as file_response:
                                    if file_response.status == 413:
                                        embed = discord.Embed(
                                            title="Error",
                                            description="413 Payload Too Large (error code: 40005): Request entity too large",
                                            color=0xff4545
                                        )
                                        await ctx.send(embed=embed)
                                        return

                                    if file_response.status == 200:
                                        file_size = int(file_response.headers.get("Content-Length", 0))
                                        if file_size > 100 * 1024 * 1024:  # 100 MB
                                            embed = discord.Embed(
                                                title="File too large",
                                                description="The file size exceeds the 100 MB limit.",
                                                color=0xff4545
                                            )
                                            await ctx.send(embed=embed)
                                            return

                                        file_content = await file_response.read()
                                        embed = discord.Embed(
                                            title="File fetched from bucket",
                                            color=discord.Color.from_str("#2BBD8E"))
                                        embed.add_field(
                                            name="File name",
                                            value=f"**`{file_name}`**",
                                            inline=False
                                        )
                                        embed.add_field(
                                            name="Bucket targeted",
                                            value=f"**`{bucket_name}`**",
                                            inline=False
                                        )
                                        await ctx.send(embed=embed)
                                        await ctx.send(file=discord.File(io.BytesIO(file_content), filename=file_name))
                                        return

                        embed = discord.Embed(
                            title="File not found",
                            description="The file could not be found by name or other attributes.",
                            color=0xff4545
                        )
                        await ctx.send(embed=embed)
                        return

                file_size = int(response.headers.get("Content-Length", 0))
                if file_size > 100 * 1024 * 1024:  # 100 MB
                    embed = discord.Embed(
                        title="File too large",
                        description="**`The file size exceeds the 100 MB limit`**",
                        color=0xff4545
                    )
                    await ctx.send(embed=embed)
                    return

                file_content = await response.read()
                embed = discord.Embed(
                    title="File fetched from bucket",
                    color=discord.Color.from_str("#2BBD8E"))
                embed.add_field(
                    name="File name",
                    value=f"**`{file_name}`**",
                    inline=False
                )
                embed.add_field(
                    name="Bucket targeted",
                    value=f"**`{bucket_name}`**",
                    inline=False
                )
                await ctx.send(embed=embed)
                await ctx.send(file=discord.File(io.BytesIO(file_content), filename=file_name))
        except Exception as e:
            embed = discord.Embed(
                title="Error",
                description=f"An error occurred: {str(e)}",
                color=0xff4545
            )
            await ctx.send(embed=embed)
            return
