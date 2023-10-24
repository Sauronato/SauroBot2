import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import Context
from youtube_search import YoutubeSearch 
import youtube_dlc as youtube_dl


# Crear una extensión separada para el reproductor de música
# Define una vista personalizada que contiene los botones
class MusicView(discord.ui.View):
    def __init__(self,cog):
        super().__init__()
        self.cog = cog

    @discord.ui.button(label="", custom_id="button-start", style=discord.ButtonStyle.primary, emoji="▶️") # the button has a custom_id set
    async def start_button_callback(self, interaction, button):
        server_id = interaction.guild_id
        await self.cog.start_stop(server_id, interaction)
        try:
            await interaction.response.defer()
        except:
            pass

    @discord.ui.button(label="", custom_id="button-skip", style=discord.ButtonStyle.primary, emoji="⏭️") # the button has a custom_id set
    async def skip_button_callback(self, interaction, button):
        server_id = interaction.guild_id
        #Añadir la comprobación de permisos
        await self.cog.skip(server_id,interaction)
        try:
            await interaction.response.defer()
        except:
            pass

    @discord.ui.button(label="", custom_id="button-exit", style=discord.ButtonStyle.danger, emoji="◻️") # the button has a custom_id set
    async def exit_button_callback(self, interaction, button):
        server_id = interaction.guild_id
        #Añadir la comprobación de permisos
        await self.cog.exit(server_id, interaction)
        try:
            await interaction.response.defer()
        except:
            pass

class MusicPlayer(commands.Cog, name="music"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.bot.database
        self.voice = {}  # Diccionario para mantener el estado de los canales de voz por servidor
        self.queue = {}  # Diccionario para mantener listas de reproducción por servidor
        self.play_channel = {}  # Canal de texto para enviar mensajes de información de la canción
        self.play_message = {}  # Mensaje de información de la canción
        self.play_role = {}  # Rol para permitir a los usuarios pausar y reanudar la canción
        self.current_song = {}  # Información de la canción actual
        self.music_view = {} #Vista de los botones de musica
        self.initializated = False
    
    async def initialize(self):
        #Revisar canales guardados en al base de datos
        canales = await self.bot.database.getMusicChannels()
        self.play_channel = canales
        #Revisar mensajes guardados en al base de datos
        mensajes = await self.bot.database.getMusicMessages()
        self.play_message = mensajes
        #Revisar roles guardados en al base de datos
        roles = await self.bot.database.getMusicRoles()
        self.play_role = roles
        #Iniciamos la cola y la voz
        for server_id in self.play_channel:
            self.queue[server_id] = []
            self.voice[server_id] = None
            self.current_song[server_id] = None
        self.bot.logger.info("MusicPlayer initialized")
        self.initializated = True

    async def start_stop(self, server_id, interaction):
        if server_id in self.voice:
            if self.initializated == False:
                await self.initialize()
            if self.voice[server_id] is None:
                return
            if self.voice[server_id].is_playing():
                self.voice[server_id].pause()
                play_channel = self.bot.get_channel(self.play_channel[server_id])
                self.bot.autodeleteMessage(play_channel, f"Canción pausada ⏸️ - <@{interaction.user}>",5,0x3498DB)
                #self.is_running = not self.is_running
            else:
                self.voice[server_id].resume()
                play_channel = self.bot.get_channel(self.play_channel[server_id])
                self.bot.autodeleteMessage(play_channel, "Canción reanudada ▶️ - <@{interaction.user}>",5,0x3498DB)
                #self.is_running = not self.is_running
        else:
            if server_id in self.queue and len(self.queue[server_id]) == 0:
                play_channel = self.bot.get_channel(self.play_channel[server_id])
                self.bot.autodeleteMessage(play_channel, "Comenzando a reproducir 🎶 - <@{interaction.user}>",5,0x3498DB)
                await self.play_next(server_id)

                #self.is_running = not self.is_runnings
            else:
                play_channel = self.bot.get_channel(self.play_channel[server_id])
                await self.bot.autodeleteMessage(play_channel, "No hay canciones en la lista de reproducción. 😞 Agrega canciones con el comando `/play`")
        

    async def skip(self, server_id):
        if server_id in self.voice:
            if self.initializated == False:
                await self.initialize()
            if self.voice[server_id] is None:
                return
            if self.voice[server_id].is_playing():
                self.voice[server_id].stop()
            else:
                return
            if len(self.queue[server_id]) > 0:
                play_channel = self.bot.get_channel(self.play_channel[server_id])
                await self.bot.autodeleteMessage(play_channel, "Saltando canción 🤸 - <@{interaction.user}>",5,0x3498DB)
                await self.play_next(server_id)
                #self.is_running = not self.is_running
            else:
                return
    async def exit(self, server_id):
        if self.initializated == False:
            await self.initialize()
        if server_id in self.voice and self.voice[server_id] is not None:
            await self.voice[server_id].disconnect()
            play_channel = self.bot.get_channel(self.play_channel[server_id])
            await self.bot.autodeleteMessage(play_channel, "¡Bye! Me fui 🌬️ - <@{interaction.user}>")
            self.voice[server_id] = None
            self.queue[server_id].clear()
            self.current_song[server_id] = None
            await self.updateSong(server_id)
        else:
            return


    @commands.hybrid_command(
            name="update",
            description="Actualiza la base de datos.",
    )
    async def show_settings(self, context: Context):
        try:
            # Obtener valores de las listas
            music_channels = self.play_channel
            music_messages = self.play_message
            music_roles = self.play_role
            music_voice = self.voice
            
            # Crear un mensaje con los contenidos de las listas
            message = "Configuración actual:\n"
            message += f"Inicializado: {self.initializated}\n"
            message += f"Canal de música: {music_channels}\n"
            message += f"Mensaje de música: {music_messages}\n"
            message += f"Rol de música: {music_roles}\n"
            message += f"Voz de música: {music_voice}\n"
            message += f"Info en BD: {await self.bot.database.get_info_server(721752348443017237)}\n"
            
            await context.send(message)
        except Exception as e:
            self.bot.logger.error(f"Error al mostrar la configuración: {e}")
            await context.send("Ha ocurrido un error al mostrar la configuración.")
    async def getEmptySong(self):
        return {
            "title": "No hay canciones en la lista de reproducción",
            "description": "Agrega canciones a la lista de reproducción con el comando `/play`",
            "thumbnail_url": "",
            "song_url": "",
            "title": "No hay canciones en la lista de reproducción",
            "thumbnail_url": "",
            "views": "",
            "author": "",
            "author_url": "",
            "duration": "",
            "song_url": "",
            "requested_by": "",
            "source": None,
        }
    async def createSong(self,title, thumbnail_url, views, author, author_url, duration, video_url, requested_by, source):
        return {
            "title": title,
            "thumbnail_url": thumbnail_url,
            "views": views,
            "author": author,
            "author_url": author_url,
            "duration": duration,
            "song_url": video_url,
            "requested_by": requested_by,
            "source": source,
        }

    async def create_music_embed(self, current_song, playlist):
        # Crear un objeto Embed
        if current_song["title"] == "No hay canciones en la lista de reproducción":
            description = "Agrega canciones a la lista de reproducción con el comando `/play`"
        else:
            description = f"De **[{current_song['author']}]({current_song['author_url'].replace(' ', '')})** dura `{current_song['duration']}`\n"
            description += f"Pedida por <@{current_song['requested_by']}>\n"
            description += f"Vistas: `{current_song['views']}`\n"
            description += f"[Ver en YouTube]({current_song['song_url']})"
        embed = discord.Embed(
            title=current_song["title"],
            description=description,
            color=0x3498DB  # Color azul
        )

        # Agregar un cuadro grande con la canción que está sonando
        embed.set_image(url=current_song["thumbnail_url"])
        # Crear una lista de canciones en la lista de reproducción
        if len(playlist) > 0 and playlist[0]["title"] != current_song["title"]:
            for i, song in enumerate(playlist):
                if song["title"] != current_song["title"]:
                    playlist_text = f"{i + 1}. {song['title']} - <@{song['requested_by']}>\n"
            embed.add_field(name="Lista de Reproducción", value=playlist_text, inline=False)
        elif len(playlist) > 10:
            playlist_text = f"Hay `{len(playlist)}`canciones en cola\n"
            embed.add_field(name="Lista de Reproducción", value=playlist_text, inline=False)
        return embed

    @commands.hybrid_command(
        name="setchannel",
        description="Asigna un canal para reproducir las canciones.",
    )
    async def setchannel(self, context: Context):
        if self.initializated == False:
            await self.initialize()
        if context.guild is None:
            await context.send("Este comando solo se puede utilizar en un servidor.")
            return
        server_id = context.guild.id

        # Verifica si el usuario que ejecutó el comando es un administrador
        if context.author.guild_permissions.administrator:
            await self.bot.database.add_server(server_id)
            self.play_channel[server_id] = context.channel.id  # Usar el ID del canal, no la mención
            await  self.bot.database.setMusicChannel(server_id, context.channel.id)
            await context.send(f'Canal de lista de reproducción establecido en {context.channel.mention}')

            # Obtener el canal de lista de reproducción
            playlist_channel = self.bot.get_channel(self.play_channel[server_id])

            if playlist_channel:
                messages = []
                # Obtiene todos los mensajes en el canal
                async for message in playlist_channel.history(limit=None):
                    messages.append(message)
                for message in messages:
                    #añadir delay
                    await asyncio.sleep(0.5)
                    await message.delete()
                song = await self.getEmptySong()
                music_embed = await self.create_music_embed(song, [])  # Sin información de la canción actual y una lista de reproducción vacía

                music_view = MusicView(self)  # Crea una instancia de tu vista
                self.music_view[server_id] = music_view
                # Agrega la vista al contenido del mensaje
                music_embed.add_field(name="Controles", value="\u200B", inline=False)
                message = await context.send(embed=music_embed, view=self.music_view[server_id])
                
                # Guarda el ID del mensaje
                self.play_message[server_id] = message.id
                await self.bot.database.setMusicMessage(server_id, message.id)
                self.queue[server_id] = []
                self.voice[server_id] = None

            else:
                await context.send('No se pudo encontrar el canal de lista de reproducción.')
        else:
            await context.send('Solo los administradores pueden configurar el canal de lista de reproducción.')

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.initializated == False:
            await self.initialize()
        playlist_channel = None
        playlist_message = None
        # Verifica si el mensaje es de un servidor
        if message.guild is not None:
            server_id = message.guild.id
            # Verifica si el servidor tiene un canal de lista de reproducción configurado
            if server_id in self.play_channel:
                playlist_channel = self.bot.get_channel(self.play_channel[server_id])
                # Verifica si el mensaje proviene del canal de lista de reproducción
                if playlist_channel is not None and message.channel == playlist_channel:
                    # Verifica si el mensaje proviene de un bot
                    if not message.author.bot:
                        # Verifica si el mensaje comienza con un comando
                        if message.content.startswith('/'):
                            await self.bot.process_commands(message)
                            await message.delete()
                        else:
                            # Aquí puedes realizar otras acciones personalizadas si no es un comando
                            await asyncio.sleep(1)
                            try:
                                await message.delete()
                            except:
                                await asyncio.sleep(1)
                                await message.delete()
                            

    @commands.hybrid_command(
        name="join",
        description="Join a voice channel.",
    )
    async def join(self, context: Context):
        server_id = context.guild.id
        if context.author.voice is not None:
            if server_id in self.voice:
                # Verificar si ya está conectado a un canal en el servidor
                await context.send("I'm already in a voice channel in this server.")
            else:
                self.voice[server_id] = await context.author.voice.channel.connect()
                self.queue[server_id] = []
        else:
            await context.send("You are not in a voice channel!")

    async def check_voice(self,ctx, bot):
        server_id = ctx.guild.id

        if server_id in bot.voice_clients:
            voice_client = bot.voice_clients[server_id]
            if voice_client.is_connected():
                voice_client.disconnect()
                self.initializated = True



    @commands.hybrid_command(
        name="play",
        description="Reproduce una canción de Youtube.",
    )
    async def play(self, context: Context, cancion: str):
            if self.initializated == False:
                await self.initialize()
            if context.guild is None:
                await self.bot.autodeleteMessage(context, "Este comando solo se puede utilizar en un servidor.")
            else:
                server_id = context.guild.id
                if server_id in self.play_channel and self.play_channel[server_id] is not None:
                    play_channel = self.bot.get_channel(self.play_channel[server_id])
                else:
                    await self.bot.autodeleteMessage(context, "No se ha configurado ningún canal de lista de reproducción. 😢")
                    return
                if context.channel != play_channel:
                    await self.bot.autodeleteMessage(context, f"Este comando solo se puede utilizar en el canal <#{play_channel.id}> 💡")
                    return
                elif context.author.voice is None:
                    await self.bot.autodeleteMessage(context, "No estás en un canal de voz. 👹")
                    return
                elif cancion == "":
                    await self.bot.autodeleteMessage(context, "Si no me das una canción, mal vamos 👹")
                    return
                elif server_id in self.voice:
                        if self.voice[server_id] is not None and self.voice[server_id].is_connected() and context.author.voice.channel.id != self.voice[server_id].channel.id:
                            await self.bot.autodeleteMessage(context, "🎉 ¡Estamos de fiesta en otro canal! 🤨 ¿No vienes o no puedes? 🤫 ")
                            return
                        else:
                            if self.voice[server_id] == None:
                                self.voice[server_id] = await context.author.voice.channel.connect()

        
            send_message = await self.bot.autodeleteMessage(context,"Buscando canción... 🔎",40,0x3498DB)

        # Utilizar youtube-search-python para buscar el video  FALTAN LAS PLAYLIST
            results = YoutubeSearch(cancion, max_results=1).to_dict()
            id = -1
            if results:
                #Se queda con el primer id que tenga mas de 0 de duración
            
                for i, result in enumerate(results):
                    duration = result["duration"]

                    if isinstance(duration, str):
                        if duration != "0":
                            id = i
                            break
                    elif isinstance(duration, int):
                        # Si ya es un entero (int), puedes usarlo directamente
                        if duration > 0:
                            id = i
                            break
                if id == -1:
                    await self.bot.autodeleteMessage(context, "No se ha encontrado ninguna canción repoducible. 😢")
                    await send_message.delete()
                    return

                video_id = results[id]["id"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                # Obtener información del video
                video_info = results[id]
                title = video_info["title"]
                duration = video_info["duration"]
                embed = discord.Embed(
                    title=f"Canción: {title}",
                    description=f"De **[{video_info['channel']}]({video_url})** dura `{duration}`\n",
                    color=0x66FF66  # Color verde
                )
                await send_message.edit(embed=embed)
                views = video_info["views"]
                # Primero, elimina la parte "Aufrufe" usando el método replace:
                views = views.replace("Aufrufe", "")
                # Luego, agrega "visitas" al final de la cadena:
                views += "visitas"
                author = video_info["channel"]
                author_url = f"https://www.youtube.com/@{video_info['channel']}"

                requested_by = context.author.id

                # Obtener la imagen de la portada del video
                thumbnail_url = video_info["thumbnails"][0]

                # Descargar y agregar a la lista de reproducción
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'opus',
                        'preferredquality': '192',
                    }],
                }
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    url2 = info['url']

                source = discord.FFmpegPCMAudio(url2)
                song = await self.createSong(title, thumbnail_url, views, author, author_url, duration, video_url, requested_by, source)
                for i, song_act in enumerate(self.queue[server_id]):
                    if song_act["title"] == title:

                        await self.bot.autodeleteMessage(context, "La canción ya está en la lista de reproducción. 😢")
                        await send_message.delete()
                        return
                self.queue[server_id].append(song)
                await send_message.delete()
                if not self.voice[server_id].is_playing() and len(self.queue[server_id]) == 1:
                    await self.play_next(server_id)
                else:
                    await self.updateSong(server_id)
                #await send_message.delete()
    async def play_next(self, server_id):
        if self.initializated == False:
            await self.initialize()
        if len(self.queue[server_id]) > 0:
            song = self.queue[server_id][0]
            source = song["source"]
            self.current_song[server_id] = song
            await self.updateSong(server_id)
            self.queue[server_id].pop(0)
            if self.voice[server_id] is not None:
                self.voice[server_id].play(source, after = lambda e: asyncio.run_coroutine_threadsafe(self.play_next(server_id), self.bot.loop))
        else:
            await self.updateSong(server_id)
            if self.voice[server_id] is not None:
                await self.voice[server_id].disconnect()
                self.voice[server_id] = None


    async def updateSong(self, server_id):
        if (self.play_channel[server_id] is not None and self.play_message[server_id] is not None):

            #Obetener siguiente canción
            if len(self.queue[server_id]) > 0:
                song = self.current_song[server_id]
            else:
                song = await self.getEmptySong()
            # Crear un objeto Embed
            music_embed = await self.create_music_embed(song, self.queue[server_id])
            # Crear una instancia de tu vista
            music_view = MusicView(self)
            if server_id in self.music_view:
                self.music_view[server_id].clear_items()
                self.music_view[server_id] = music_view
                # Edita el mensaje con la nueva información
                playlist_channel = self.bot.get_channel(self.play_channel[server_id])
                playlist_message = await playlist_channel.fetch_message(self.play_message[server_id])
                await playlist_message.edit(embed=music_embed, view = self.music_view[server_id])
                return
            else:
                self.music_view[server_id] = music_view
                playlist_channel = self.bot.get_channel(self.play_channel[server_id])
                playlist_message = await playlist_channel.fetch_message(self.play_message[server_id])
                await playlist_message.delete()
                playlist_message = await playlist_channel.send(embed=music_embed, view = self.music_view[server_id])
                self.play_message[server_id] = playlist_message.id
                await self.bot.database.setMusicMessage(server_id, playlist_message.id)              


    @commands.hybrid_command(
        name="leave",
        description="Leave the voice channel.",
    )
    async def leave(self, context: Context):
        server_id = context.guild.id
        if server_id in self.voice:
            if self.voice[server_id].is_connected():
                await self.voice[server_id].disconnect()
                self.voice[server_id] = None
                self.queue[server_id] = []
            else:
                await context.send("I'm not in a voice channel.")
        else:
            await context.send("I'm not in a voice channel.")


# Agrega la extensión al bot
async def setup(bot) -> None:
    await bot.add_cog(MusicPlayer(bot))




