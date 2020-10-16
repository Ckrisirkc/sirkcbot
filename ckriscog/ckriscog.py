from redbot.core import commands, checks, Config
from redbot.cogs.audio.audio_dataclasses import LocalPath, Query
import discord
import logging
import asyncio
import random
import lavalink
import os
import re

log = logging.getLogger('red.ckriscogs')

class Ckriscog(commands.Cog):
    """Self made commands by Ckris"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=98117117430, force_registration=True)
        default_guild = { 
                    "role_required": 494761369191710721,
                    "regular_role": 154451438339096577
                    }
        default_channel = {
                    "is_role_channel": False,
                    "prune_channel_messages": False,
                    "prune_message_delay": 20
                    }
        #
        self.config.register_guild(**default_guild)
        self.config.register_channel(**default_channel)
    #
    
    
    async def _delAfterTime(self, msgs, time=30):
        #await asyncio.sleep(time)
        for msg in msgs:
            try:
                #await self.bot.delete_message(msg)
                log.info(f'Deleting message by {msg.author}, content: {msg.content}')
                await msg.delete(delay=time)
            except discord.Forbidden:
                log.debug("Cannot delete message, Forbidden")
            except discord.NotFound:
                log.debug("Cannot delete message, Not Found")
            except discord.HTTPException:
                log.debug('Delete failed')
    #
    
    
    @commands.guild_only()
    @commands.command()
    @checks.admin_or_permissions(move_members=True)
    async def massmove(self, ctx, from_channel: discord.VoiceChannel, to_channel: discord.VoiceChannel):
        """Massmove users to another voice channel"""
        await self._massmove(ctx, from_channel, to_channel)

    async def _massmove(self, ctx, from_channel, to_channel):
        """Internal function: Massmove users to another voice channel"""
        # check if channels are voice channels. Or moving will be very... interesting...
        type_from = str(from_channel.type)
        type_to = str(to_channel.type)
        if type_from != 'voice':
            await ctx.send('{} is not a valid voice channel'.format(from_channel.name))
            log.debug('SID: {}, from_channel not a voice channel'.format(from_channel.guild.id))
        elif type_to != 'voice':
            await ctx.send('{} is not a valid voice channel'.format(to_channel.name))
            log.debug('SID: {}, to_channel not a voice channel'.format(to_channel.guild.id))
        else:
            try:
                log.debug('Starting move on SID: {}'.format(from_channel.guild.id))
                log.debug('Getting copy of current list to move')
                voice_list = list(from_channel.members)
                for member in voice_list:
                    await member.edit(voice_channel = to_channel, reason=f'MassMove by {ctx.message.author}')
                    log.debug('Member {} moved to channel {}'.format(member.id, to_channel.id))
                    await asyncio.sleep(0.05)
            except discord.Forbidden:
                await ctx.send('I have no permission to move members.')
            except discord.HTTPException:
                await ctx.send('A error occured. Please try again')
    #
    
    @commands.guild_only()
    @commands.group(invoke_without_command=True)
    async def regular(self, ctx, request_for : discord.Member):
        """Add the Regular role to a member"""
        
        proper_channel = await self.config.channel(ctx.channel).is_role_channel()
        proper_role_id = await self.config.guild(ctx.guild).role_required()
        regular_role_id = await self.config.guild(ctx.guild).regular_role()
        proper_role = ctx.guild.get_role(proper_role_id)
        
        if proper_role is None:
            msg = await ctx.send('Please set the role required to run the command first')
            await self._delAfterTime([ctx.message, msg])
            return
        #
        if not proper_channel:
            msg = await ctx.send('This command is not valid in this channel')
            await self._delAfterTime([ctx.message, msg])
            return
        #
        if not proper_role in ctx.author.roles:
            msg = await ctx.send('You do not have the proper role for this command')
            await self._delAfterTime([ctx.message, msg])
            return
        #
        reg_role = ctx.guild.get_role(regular_role_id)
        current_roles = request_for.roles
        if reg_role in current_roles:
            msg = await ctx.send('The user already has the Regular role')
            await self._delAfterTime([ctx.message, msg])
            #printroles = ','.join([role.name for role in current_roles])
            #await ctx.send(f'Roles: {printroles}')
            return
        else:
            current_roles.append(reg_role)
            try:
                await request_for.edit(roles=current_roles)
                msg = await ctx.send(f'Added the Regular role to {request_for}')
                await self._delAfterTime([ctx.message, msg])
                log.info(f'Member {ctx.author} gave the Regular role to {request_for}')
            except discord.Forbidden:
                msg = await ctx.send('Error, cannot give roles')
                await self._delAfterTime([ctx.message, msg])
            #
        #
    #
    @regular.command()
    @commands.guild_only()
    @checks.admin()
    async def setChannel(self, ctx, chan : discord.TextChannel):
        """Sets the channel for requesting the regular role"""
        is_role_channel = await self.config.channel(chan).is_role_channel()
        await self.config.channel(chan).is_role_channel.set(not is_role_channel)
        if not is_role_channel:
            await ctx.send('Set the channel to be a role channel')
        else:
            await ctx.send('Removed the channel as a role channel')
        #
    #
    
    @commands.group(invoke_without_command=True)
    #@commands.command()
    @commands.guild_only()
    @checks.admin()
    async def pruneMessages(self, ctx, chan : discord.TextChannel):
        """Toggle the pruning of messages in a given text channel"""
        is_prune_channel = await self.config.channel(chan).prune_channel_messages()
        await self.config.channel(chan).prune_channel_messages.set(not is_prune_channel)
        if not is_prune_channel:
            await ctx.send(f'Now pruning messages in {chan}')
        else:
            await ctx.send(f'Disabled pruning messages in {chan}')
        #
    #
    @pruneMessages.command()
    @commands.guild_only()
    @checks.admin()
    async def delay(self, ctx, chan : discord.TextChannel, time_in_seconds : int):
        """Set the prune delay for channel to time_in_seconds"""
        await self.config.channel(chan).prune_message_delay.set(time_in_seconds)
        await ctx.send(f"Set the prune delay for {chan} to {time_in_seconds} seconds")
    #
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if isinstance(message.channel, discord.abc.PrivateChannel):
            return
        #
        #if message.author.bot:
        #    return
        #await self.check_fuck(message)
        chan = message.channel
            
        is_prune_channel = await self.config.channel(chan).prune_channel_messages()
        log.info(f"on_message: {chan != 187792525258391552},{message.guild == 154442858525491201},{not is_prune_channel}")
        if chan != 187792525258391552 and message.guild == 154442858525491201 and not is_prune_channel:
            if message.author.bot and message.author != 196382897366761472:
                await self._delAfterTime([message])
                return
            if re.match(r"^!(help|.{1,17} \d\d?)$"):
                await asyncio.sleep(2)
                msg = await message.channel.send("Please enter bot commands in #bot-stuff")
                await self._delAfterTime([message, msg])
                return
        #
        if not is_prune_channel:
            return
        #
        log.info(f'Deleting message by {message.author.name} in {chan}, content: {message.content}')
        del_delay = await self.config.channel(chan).prune_message_delay()
        await message.delete(delay=del_delay)
    #
    @commands.guild_only()
    @commands.command()
    async def base(self, ctx):
        return
        sender = ctx.author
        sounddir = os.path.join(os.getcwd(), 'soundfiles')
        myfile = os.path.join(sounddir, os.listdir(sounddir)[0])
        if sender.voice is None or sender.voice.channel is None:
            await ctx.send(f"You're not in any voice channel")
            #log.info(f"Current directory: {os.getcwd()}")
            return
        audio = self.bot.get_cog("Audio")
        failed = await ctx.invoke(audio.command_summon)
        if failed or True:
            return
        #lavaplayer = lavalink.get_player(ctx.guild.id)
        ##lavaplayer.store("channel", ctx.channel.id)
        #await lavaplayer.stop()
        #localfolder = LocalPath.joinpath(sounddir, '')
        #query = Query.process_input(sounddir,
        #track = load_result.tracks[0]
        #await lavaplayer.add(sender,track)
        #await lavaplayer.play()
        
        
        
        

    async def check_fuck(self, message: discord.Message):
        if 'fuck' in message.content.lower() and message.guild.id == 154442858525491201 and not message.author.bot:
            await message.channel.send(random.choice(['Watch your language, motherfucker', 'Calm the fuck down', 'Stop fucking around']))
            