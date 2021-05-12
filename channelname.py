from __future__ import annotations

import typing as ty
import aurflux
import discord
import collections as clc
import asyncio as aio
import aurflux.auth
import aurcore as aur
import aurflux.context


class RenameHandler(aurflux.FluxCog):
   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.locks: ty.Dict[str, aio.Lock] = clc.defaultdict(aio.Lock)

   def load(self):

      @self._commandeer(name="rename", default_auths=[aurflux.auth.Record.allow_all()])
      async def __hb(ctx: aurflux.ty.GuildCommandCtx, args):
         """
         rename name
         ==
         changes the channel name of <#699733726552260701> to `name`
         ==
         name: channel name
         ==
         :param ctx:
         :return:
         """
         channel = await self.flux.get_channel_s(699733726552260701)
         assert isinstance(channel, discord.TextChannel)
         await channel.edit(name=args, reason=f"Changed by [{ctx.author_ctx.author.id}] {ctx.author_ctx.author}")