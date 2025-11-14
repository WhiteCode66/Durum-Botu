import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
from datetime import datetime

# Bot ayarları
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Sunucu ayarları için sözlük (sunucu_id: {"rol": rol_id, "durum": "aranan_text", "log_kanal": kanal_id})
sunucu_ayarlari = {}

@bot.event
async def on_ready():
    print(f'✅ {bot.user} aktif!')
    print(f'🔗 Bot {len(bot.guilds)} sunucada!')
    
    # Slash komutları senkronize et
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} slash komutu senkronize edildi!')
    except Exception as e:
        print(f'❌ Komutlar senkronize edilemedi: {e}')
    
    # Durum kontrolünü başlat
    if not durum_kontrol.is_running():
        durum_kontrol.start()
        print('✅ Durum kontrol sistemi başlatıldı!')

# MANUEL AYAR: /durumrol @rol
@bot.tree.command(name="durumrol", description="Verilecek rolü ayarla")
@app_commands.describe(rol="Verilecek rol")
async def durumrol(interaction: discord.Interaction, rol: discord.Role):
    # Sadece yöneticiler kullanabilir
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yönetici olmalısın!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    # Ayarları kaydet
    if guild_id not in sunucu_ayarlari:
        sunucu_ayarlari[guild_id] = {}
    
    sunucu_ayarlari[guild_id]["rol"] = rol.id
    
    await interaction.response.send_message(
        f"✅ **Durum Rolü Ayarlandı!**\n"
        f"🎭 Rol: {rol.mention}\n"
        f"📝 Şimdi `/durum` komutuyla kontrol edilecek durumu belirle!\n"
        f"📋 `/logkanal` komutuyla log kanalını ayarlayabilirsin!",
        ephemeral=True
    )

# MANUEL AYAR: /logkanal #kanal
@bot.tree.command(name="logkanal", description="Log kanalını ayarla")
@app_commands.describe(kanal="Log mesajlarının gönderileceği kanal")
async def logkanal(interaction: discord.Interaction, kanal: discord.TextChannel):
    # Sadece yöneticiler kullanabilir
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yönetici olmalısın!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    # Ayarları kaydet
    if guild_id not in sunucu_ayarlari:
        sunucu_ayarlari[guild_id] = {}
    
    sunucu_ayarlari[guild_id]["log_kanal"] = kanal.id
    
    await interaction.response.send_message(
        f"✅ **Log Kanalı Ayarlandı!**\n"
        f"📋 Kanal: {kanal.mention}\n"
        f"🤖 Rol verme/alma işlemleri bu kanala kaydedilecek!",
        ephemeral=True
    )

# MANUEL AYAR: /durum metin
@bot.tree.command(name="durum", description="Kontrol edilecek durumu ayarla")
@app_commands.describe(metin="Aranacak durum metni (örn: /rakipsiz)")
async def durum(interaction: discord.Interaction, metin: str):
    # Sadece yöneticiler kullanabilir
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yönetici olmalısın!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    # Ayarları kaydet
    if guild_id not in sunucu_ayarlari:
        sunucu_ayarlari[guild_id] = {}
    
    sunucu_ayarlari[guild_id]["durum"] = metin.lower()
    
    # Rol kontrolü
    rol_id = sunucu_ayarlari[guild_id].get("rol")
    if rol_id:
        rol = interaction.guild.get_role(rol_id)
        rol_text = rol.mention if rol else "❌ Rol bulunamadı!"
    else:
        rol_text = "❌ Henüz rol ayarlanmadı! `/durumrol` komutuyla rol belirle."
    
    await interaction.response.send_message(
        f"✅ **Durum Kontrolü Ayarlandı!**\n"
        f"📝 Aranan Durum: `{metin}`\n"
        f"🎭 Verilecek Rol: {rol_text}\n\n"
        f"🤖 Bot artık her 30 saniyede bu durumu olan üyelere rol verecek!\n"
        f"⚠️ Durumu kaldıran üyelerden rol otomatik alınacak!",
        ephemeral=True
    )

# AYARLARI GÖRÜNTÜLE: /ayarlar
@bot.tree.command(name="ayarlar", description="Mevcut durum kontrol ayarlarını göster")
async def ayarlar(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    
    if guild_id not in sunucu_ayarlari or not sunucu_ayarlari[guild_id]:
        await interaction.response.send_message(
            "❌ **Henüz ayar yapılmamış!**\n\n"
            "**Kurulum:**\n"
            "1. `/durumrol @rol` - Verilecek rolü belirle\n"
            "2. `/durum metin` - Kontrol edilecek durumu belirle\n"
            "3. `/logkanal #kanal` - Log kanalını belirle (opsiyonel)",
            ephemeral=True
        )
        return
    
    ayar = sunucu_ayarlari[guild_id]
    rol_id = ayar.get("rol")
    durum_text = ayar.get("durum", "❌ Belirlenmedi")
    log_kanal_id = ayar.get("log_kanal")
    
    if rol_id:
        rol = interaction.guild.get_role(rol_id)
        rol_text = rol.mention if rol else "❌ Rol bulunamadı!"
    else:
        rol_text = "❌ Belirlenmedi"
    
    if log_kanal_id:
        log_kanal = interaction.guild.get_channel(log_kanal_id)
        log_text = log_kanal.mention if log_kanal else "❌ Kanal bulunamadı!"
    else:
        log_text = "❌ Belirlenmedi"
    
    await interaction.response.send_message(
        f"⚙️ **Durum Kontrol Ayarları**\n\n"
        f"📝 Aranan Durum: `{durum_text}`\n"
        f"🎭 Verilecek Rol: {rol_text}\n"
        f"📋 Log Kanalı: {log_text}\n"
        f"⏱️ Kontrol Sıklığı: Her 30 saniye\n\n"
        f"**Komutlar:**\n"
        f"`/durumrol @rol` - Rolü değiştir\n"
        f"`/durum metin` - Durumu değiştir\n"
        f"`/logkanal #kanal` - Log kanalını değiştir\n"
        f"`/manuelkontrol` - Şimdi kontrol et",
        ephemeral=True
    )

# MANUEL KONTROL: /manuelkontrol
@bot.tree.command(name="manuelkontrol", description="Şimdi durum kontrolü yap")
async def manuelkontrol(interaction: discord.Interaction):
    # Sadece yöneticiler kullanabilir
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Bu komutu kullanmak için yönetici olmalısın!", ephemeral=True)
        return
    
    guild_id = interaction.guild.id
    
    if guild_id not in sunucu_ayarlari or not sunucu_ayarlari[guild_id].get("rol") or not sunucu_ayarlari[guild_id].get("durum"):
        await interaction.response.send_message(
            "❌ Önce ayarları yapmalısın!\n"
            "`/durumrol @rol` ve `/durum metin` komutlarını kullan.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    
    # Kontrol yap
    verilen, alinan = await durum_kontrolu_yap(interaction.guild)
    
    await interaction.followup.send(
        f"✅ **Manuel Kontrol Tamamlandı!**\n\n"
        f"➕ Rol Verilen: **{verilen}** üye\n"
        f"➖ Rol Alınan: **{alinan}** üye",
        ephemeral=True
    )

# LOG GÖNDERME FONKSİYONU
async def log_gonder(guild, embed):
    """Log kanalına embed mesajı gönderir"""
    guild_id = guild.id
    
    if guild_id not in sunucu_ayarlari:
        return
    
    log_kanal_id = sunucu_ayarlari[guild_id].get("log_kanal")
    if not log_kanal_id:
        return
    
    log_kanal = guild.get_channel(log_kanal_id)
    if not log_kanal:
        return
    
    try:
        await log_kanal.send(embed=embed)
    except Exception as e:
        print(f"❌ Log gönderilemedi: {e}")

# OTOMATIK DURUM KONTROLÜ (Her 30 saniyede bir)
@tasks.loop(seconds=30)
async def durum_kontrol():
    for guild in bot.guilds:
        try:
            await durum_kontrolu_yap(guild)
        except Exception as e:
            print(f'❌ {guild.name} sunucusunda hata: {e}')

async def durum_kontrolu_yap(guild):
    """Bir sunucuda durum kontrolü yapar"""
    guild_id = guild.id
    
    # Ayar yoksa geç
    if guild_id not in sunucu_ayarlari:
        return 0, 0
    
    ayar = sunucu_ayarlari[guild_id]
    rol_id = ayar.get("rol")
    aranan_durum = ayar.get("durum")
    
    # Ayarlar eksikse geç
    if not rol_id or not aranan_durum:
        return 0, 0
    
    rol = guild.get_role(rol_id)
    if not rol:
        return 0, 0
    
    verilen_sayisi = 0
    alinan_sayisi = 0
    
    # Tüm üyeleri kontrol et
    for member in guild.members:
        if member.bot:
            continue
        
        # Üyenin custom durumunu al
        custom_status = None
        for activity in member.activities:
            if isinstance(activity, discord.CustomActivity):
                custom_status = activity.name
                break
        
        # Durumu kontrol et
        durum_var = False
        if custom_status:
            durum_var = aranan_durum.lower() in custom_status.lower()
        
        # Rol işlemleri
        has_role = rol in member.roles
        
        if durum_var and not has_role:
            # Durumu var ama rolü yok -> Rol ver
            try:
                await member.add_roles(rol, reason=f"Durumda '{aranan_durum}' bulundu")
                verilen_sayisi += 1
                print(f"✅ {member.name} -> Rol verildi (Durum: {custom_status})")
                
                # Log gönder
                embed = discord.Embed(
                    title="✅ Rol Verildi",
                    description=f"{member.mention} kullanıcısına {rol.mention} rolü verildi.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="👤 Üye", value=f"{member.mention} (`{member.id}`)", inline=True)
                embed.add_field(name="🎭 Rol", value=rol.mention, inline=True)
                embed.add_field(name="📝 Durum", value=f"`{custom_status}`", inline=False)
                embed.set_thumbnail(url=member.display_avatar.url)
                await log_gonder(guild, embed)
                
            except Exception as e:
                print(f"❌ {member.name} -> Rol verilemedi: {e}")
        
        elif not durum_var and has_role:
            # Durumu yok ama rolü var -> Rolü al
            try:
                await member.remove_roles(rol, reason=f"Durumda '{aranan_durum}' bulunamadı")
                alinan_sayisi += 1
                print(f"➖ {member.name} -> Rol alındı")
                
                # Log gönder
                embed = discord.Embed(
                    title="➖ Rol Alındı",
                    description=f"{member.mention} kullanıcısından {rol.mention} rolü alındı.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="👤 Üye", value=f"{member.mention} (`{member.id}`)", inline=True)
                embed.add_field(name="🎭 Rol", value=rol.mention, inline=True)
                embed.add_field(name="📝 Sebep", value="Durumdan kaldırıldı", inline=False)
                embed.set_thumbnail(url=member.display_avatar.url)
                await log_gonder(guild, embed)
                
            except Exception as e:
                print(f"❌ {member.name} -> Rol alınamadı: {e}")
    
    if verilen_sayisi > 0 or alinan_sayisi > 0:
        print(f"📊 {guild.name}: +{verilen_sayisi} rol verildi, -{alinan_sayisi} rol alındı")
    
    return verilen_sayisi, alinan_sayisi

@durum_kontrol.before_loop
async def before_durum_kontrol():
    await bot.wait_until_ready()

# BOTU BAŞLAT
bot.run('TOKEN_BURAYA')
