from __future__ import annotations

import asyncio
import contextlib
from loguru import logger
import aurflux
# import aiohttp
import aurcore as aur
import typing as ty
import TOKENS
import heartboard
import discord
import channelname
aur.log.setup()
intents = discord.Intents.none()
intents.guilds = True
intents.messages = True
intents.reactions = True
intents.members = True
intents.presences = True


slowbro = aurflux.FluxCore(name="slowbro", admin_id=TOKENS.ADMIN_ID, intents=intents)

slowbro.flux.register_cog(heartboard.HBHandler)
slowbro.flux.register_cog(channelname.RenameHandler)
aur.aiorun(slowbro.startup(token=TOKENS.SLOWBRO), slowbro.shutdown())
