from __future__ import annotations

import typing as ty
import aurflux
import discord
import itertools as itt
import collections as clc
import asyncio as aio
import aurflux.auth
import aurcore as aur
import aurflux.context

if ty.TYPE_CHECKING:
   import datetime
from aurflux.command import Response

VIDEO_EXTS = ["3g2", "3gp", "aaf", "asf", "avchd", "avi", "drc", "flv", "m2v", "m4p", "m4v", "mkv", "mng", "mov", "mp2", "mp4", "mpe", "mpeg", "mpg", "mpv", "mxf", "nsv", "ogg",
              "ogv", "qt", "rm", "rmvb", "roq", "svi", "vob", "webm", "wmv", "yuv"]
IMAGE_EXTS = ["ase", "art", "bmp", "blp", "cd5", "cit", "cpt", "cr2", "cut", "dds", "dib", "djvu", "egt", "exif", "gif", "gpl", "grf", "icns", "ico", "iff", "jng", "jpeg", "jpg",
              "jfif", "jp2", "jps", "lbm", "max", "miff", "mng", "msp", "nitf", "ota", "pbm", "pc1", "pc2", "pc3", "pcf", "pcx", "pdn", "pgm", "PI1", "PI2", "PI3", "pict", "pct",
              "pnm", "pns", "ppm", "psb", "psd", "pdd", "psp", "px", "pxm", "pxr", "qfx", "raw", "rle", "sct", "sgi", "rgb", "int", "bw", "tga", "tiff", "tif", "vtf", "xbm", "xcf",
              "xpm", "3dv", "amf", "ai", "awg", "cgm", "cdr", "cmx", "dxf", "e2d", "egt", "eps", "fs", "gbr", "odg", "svg", "stl", "vrml", "x3d", "sxd", "v2d", "vnd", "wmf", "emf",
              "art", "xar", "png", "webp", "jxr", "hdp", "wdp", "cur", "ecw", "iff", "lbm", "liff", "nrrd", "pam", "pcx", "pgf", "sgi", "rgb", "rgba", "bw", "int", "inta", "sid",
              "ras", "sun", "tga"]


def message2embed(message: discord.Message, embed_color: discord.Color = None):
   embeds = []

   for m, embed in itt.zip_longest([message], [*message.embeds, *message.attachments], fillvalue=None):

      new_embed = discord.Embed()
      if isinstance(embed, discord.Embed) and (embed.title or embed.description):
         new_embed = embed
         new_embed.description = (str(new_embed.description) if new_embed.description != discord.Embed.Empty else "") + f"\n\n[Jump to message]({message.jump_url})"
         embeds.append(new_embed)
         continue

      if m:
         new_embed.timestamp = m.created_at

         new_embed.set_author(name=m.author.name, icon_url=m.author.avatar_url, url=m.jump_url)
         new_embed.description = f"{m.content[:1900] + ('...' if len(m.content) > 1900 else '')}"
         new_embed.set_footer(text=f"#{m.channel.name} | Sent at {m.created_at.isoformat('@').replace('@', ' at ')[:-7]}")
      if isinstance(embed, discord.Attachment):
         if any(embed.url.endswith(ext) for ext in IMAGE_EXTS):
            new_embed.set_image(url=embed.url)
         else:
            new_embed.description = new_embed.description or ""
            new_embed.description += f"\n{embed.url}"
      if isinstance(embed, discord.Embed) and embed.url:
         if embed.thumbnail:
            new_embed.set_image(url=embed.thumbnail.url)
         else:
            new_embed.set_image(url=embed.url)

      new_embed.description = (str(new_embed.description) if new_embed.description != discord.Embed.Empty else "") + f"\n\n[Jump to message]({message.jump_url})"

      embeds.append(new_embed)

   return embeds


class HBHandler(aurflux.FluxCog):
   def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.locks: ty.Dict[str, aio.Lock] = clc.defaultdict(aio.Lock)
      self.messages :ty.Set[int] = set()

   def load(self):
      @self.router.listen_for("flux:reaction_add")
      @aur.Eventful.decompose
      async def reaction_handler(reaction: discord.Reaction, user: ty.Union[discord.Member, discord.User]):
         if reaction.emoji != "❤️":
            return
         if not reaction.message.guild:
            return
         config = self.flux.CONFIG.of(aurflux.context.ManualGuildCtx(flux=self.flux, guild=reaction.message.guild))
         if reaction.count < config["heartboard_num"]:
            return
         if reaction.message.id in self.messages:
            return
         self.messages.add(reaction.message.id)
         channel = await self.flux.get_channel_s(config["heartboard_target"])
         assert isinstance(channel, discord.TextChannel)

         [await channel.send(embed=e) for e in message2embed(reaction.message)]

      @self._commandeer(name="hb", default_auths=[aurflux.auth.Record.allow_server_manager()])
      async def __hb(ctx: aurflux.ty.GuildCommandCtx, args):
         """
         hb [num/channel] (value)
         ==
         Gets/Sets a heartboard setting
         ==
         [num/channel] : `num` gets/sets threshold of reactions to be pinned, `channel` gets/sets target channel
         ==
         :param ctx:
         :return:
         """
         configs = self.flux.CONFIG.of(ctx.msg_ctx)
         if not args:
            raise aurflux.errors.CommandSyntaxError("hb",configs["prefix"])
         config_type, target, *_ = args.split(" ") + [None, None]

         if not config_type:
            raise aurflux.errors.CommandSyntaxError("hb", configs["prefix"])

         async with self.flux.CONFIG.writeable_conf(ctx.msg_ctx) as cfg:
            if "number".startswith(config_type):
               if not target:
                  return Response(embed=discord.Embed(title="Heartboard Reaction # Threshold", description=f"<#{configs['heartboard_num']}>)"))
               cfg["heartboard_num"] = int(target)
               return Response(content=f"Heartboard Reaction # Threshold set to: `{target}`")

            if "channel".startswith(config_type):
               if not target:
                  return Response(embed=discord.Embed(title="Heartboard Target", description=f"<#{configs['heartboard_target']}>)"))
               target = aurflux.utils.find_mentions(target)
               if not target:
                  raise aurflux.errors.CommandError(f"No channels found in: `{target}`")
               target = target[0]
               channel = await self.flux.get_channel_s(target)
               if not channel or not isinstance(channel, discord.TextChannel) or channel.guild != ctx.msg_ctx.guild:
                  raise aurflux.errors.CommandError(f"`target` was not recognized as a text channel in this server")
               cfg["heartboard_target"] = target
               return Response(content=f"Heartboard Target channel set to: <#{target}>")