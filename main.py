import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import routeros_api

# --- KONFIGURASI ---
TELEGRAM_TOKEN = 'MASUKKAN_TOKEN_BOT_ANDA_DISINI'
ADMIN_CHAT_ID = 12345678   # Chat ID Telegram

MIKROTIK_IP = '10.10.10.1'
MIKROTIK_USER = 'user_mikrotik'
MIKROTIK_PASS = 'password_mikrotik'
# -------------------

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_data = {}

def is_admin(chat_id):
    return chat_id == ADMIN_CHAT_ID

# --- 1. MEMBUAT MENU UTAMA ---
@bot.message_handler(commands=['start', 'menu'])
def main_menu(message):
    if not is_admin(message.chat.id): return
    
    markup = InlineKeyboardMarkup(row_width=2)
    btn_filter = InlineKeyboardButton("🛡 Firewall Filter", callback_data="menu_filter")
    btn_nat = InlineKeyboardButton("🌐 Konfigurasi NAT", callback_data="menu_nat")
    btn_mangle = InlineKeyboardButton("🔀 Konfigurasi Mangle", callback_data="menu_mangle")
    btn_addr = InlineKeyboardButton("📋 Address List", callback_data="menu_addr")
    
    markup.add(btn_filter, btn_nat, btn_mangle, btn_addr)
    
    bot.send_message(
        message.chat.id, 
        "🎛 **Panel Kontrol MikroTik**\nPilih menu konfigurasi di bawah ini:", 
        reply_markup=markup, 
        parse_mode="Markdown"
    )

# --- 2. MENANGKAP KLIK TOMBOL (CALLBACK HANDLER) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if not is_admin(chat_id): return
    
    if chat_id not in user_data:
        user_data[chat_id] = {}

    # === ALUR SUB-MENU FILTER ===
    if call.data == "menu_filter":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("⚡ Template Cepat", callback_data="flt_tpl"),
            InlineKeyboardButton("⚙️ Custom Rule", callback_data="flt_custom")
        )
        bot.send_message(chat_id, "Pilih mode pembuatan Firewall Filter:", reply_markup=markup)

    elif call.data == "flt_tpl":
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Drop Invalid Packets (Forward)", callback_data="flt_do_invalid"),
            InlineKeyboardButton("Block Ping / ICMP (Input)", callback_data="flt_do_icmp")
        )
        bot.send_message(chat_id, "Pilih template rule yang ingin diterapkan:", reply_markup=markup)

    elif call.data == "flt_do_invalid":
        execute_filter_template(chat_id, chain="forward", action="drop", connection_state="invalid", comment="Drop Invalid (By Bot)")
    
    elif call.data == "flt_do_icmp":
        execute_filter_template(chat_id, chain="input", action="drop", protocol="icmp", comment="Block ICMP (By Bot)")

    elif call.data == "flt_custom":
        markup = InlineKeyboardMarkup(row_width=3)
        markup.add(
            InlineKeyboardButton("Input", callback_data="flt_chain_input"),
            InlineKeyboardButton("Forward", callback_data="flt_chain_forward"),
            InlineKeyboardButton("Output", callback_data="flt_chain_output")
        )
        bot.send_message(chat_id, "⚙️ **Custom Rule - Step 1: Pilih Chain**", reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("flt_chain_"):
        chain = call.data.split("_")[2]
        user_data[chat_id]['flt_chain'] = chain
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("✅ Accept", callback_data="flt_act_accept"),
            InlineKeyboardButton("❌ Drop", callback_data="flt_act_drop")
        )
        bot.send_message(chat_id, f"Chain: `{chain}`\n\n**Step 2: Pilih Action**", reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("flt_act_"):
        action = call.data.split("_")[2]
        user_data[chat_id]['flt_action'] = action
        
        msg = bot.send_message(chat_id, f"Action: `{action}`\n\n**Step 3: Ketik IP Source Target**\n(Contoh: `10.10.10.50` atau ketik `all` untuk semua IP):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_filter_ip)

    # === ALUR SUB-MENU NAT ===
    elif call.data == "menu_nat":
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🌐 Masquerade (SrcNAT)", callback_data="nat_masq"),
            InlineKeyboardButton("🚪 Port Forward (DstNAT)", callback_data="nat_dst")
        )
        bot.send_message(chat_id, "Pilih tipe NAT yang ingin dibuat:", reply_markup=markup)

    elif call.data == "nat_masq":
        msg = bot.send_message(chat_id, "Ketik *IP Network* yang ingin di-Masquerade (contoh: 10.10.10.0/24):", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_nat_masq)
        
    elif call.data == "nat_dst":
        text_bantuan = "Ketik parameter Port Forwarding.\n**Format:** `IP_Tujuan Port_Tujuan IP_Lokal Port_Lokal`\n**Contoh:** `103.x.x.x 8080 10.10.10.50 80`"
        msg = bot.send_message(chat_id, text_bantuan, parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_nat_dst)

    # === ALUR SUB-MENU MANGLE ===
    elif call.data == "menu_mangle":
        markup = InlineKeyboardMarkup(row_width=3)
        markup.add(
            InlineKeyboardButton("Prerouting", callback_data="mgl_chain_prerouting"),
            InlineKeyboardButton("Forward", callback_data="mgl_chain_forward"),
            InlineKeyboardButton("Postrouting", callback_data="mgl_chain_postrouting")
        )
        bot.send_message(chat_id, "🔀 **Step 1: Pilih Chain Mangle**", reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("mgl_chain_"):
        chain = call.data.split("_")[2]
        user_data[chat_id]['mangle_chain'] = chain
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("🔗 Mark Connection", callback_data="mgl_act_mark-connection"),
            InlineKeyboardButton("📦 Mark Packet", callback_data="mgl_act_mark-packet"),
            InlineKeyboardButton("🛣 Mark Routing", callback_data="mgl_act_mark-routing")
        )
        bot.send_message(chat_id, f"Chain: `{chain}`\n\n**Step 2: Pilih Action**", reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("mgl_act_"):
        action = call.data.split("_")[2]
        user_data[chat_id]['mangle_action'] = action
        msg = bot.send_message(chat_id, f"Action: `{action}`\n\n**Step 3: Ketik IP Source Target** (contoh: 10.10.10.10) atau ketik `all`:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_mangle_ip)

    # === ALUR SUB-MENU ADDRESS LIST ===
    elif call.data == "menu_addr":
        bot.send_message(chat_id, "⏳ Mengambil data Address List dari MikroTik...")
        try:
            connection = routeros_api.RouterOsApiPool(MIKROTIK_IP, username=MIKROTIK_USER, password=MIKROTIK_PASS, plaintext_login=True)
            existing_lists = connection.get_api().get_resource('/ip/firewall/address-list').get()
            connection.disconnect()

            unique_list_names = set(item['list'] for item in existing_lists if 'list' in item)
            list_text = "\n".join([f"• `{name}`" for name in unique_list_names]) if unique_list_names else "_Belum ada list._"

            msg = bot.send_message(chat_id, f"📋 **Address List Existing:**\n{list_text}\n\n👉 Ketik **Nama List** (Pilih dari atas atau buat baru):", parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_address_list_name)
        except Exception as e:
            bot.send_message(chat_id, f"❌ **Gagal:**\n`{e}`", parse_mode="Markdown")

    bot.answer_callback_query(call.id)

# --- 3. PROSES BERTAHAP (STATE MACHINE) ---

# --- A. FUNGSI FILTER ---
def execute_filter_template(chat_id, **kwargs):
    bot.send_message(chat_id, "⏳ Mengeksekusi Template Firewall...")
    try:
        connection = routeros_api.RouterOsApiPool(MIKROTIK_IP, username=MIKROTIK_USER, password=MIKROTIK_PASS, plaintext_login=True)
        connection.get_api().get_resource('/ip/firewall/filter').add(**kwargs)
        connection.disconnect()
        bot.send_message(chat_id, f"✅ **Template Berhasil Diterapkan!**\nAturan telah ditambahkan ke Firewall Filter.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Gagal: `{e}`", parse_mode="Markdown")

def process_filter_ip(message):
    if not is_admin(message.chat.id): return
    chat_id = message.chat.id
    user_data[chat_id]['flt_ip'] = message.text.strip()
    
    msg = bot.send_message(chat_id, "**Step 4: Ketik Protocol & Port**\nContoh: `tcp 80` atau `icmp` atau ketik `all` untuk semua traffic:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_filter_execute)

def process_filter_execute(message):
    if not is_admin(message.chat.id): return
    chat_id = message.chat.id
    proto_port = message.text.strip().lower()
    
    data = user_data.get(chat_id, {})
    chain = data.get('flt_chain')
    action = data.get('flt_action')
    ip_target = data.get('flt_ip')
    
    if not chain or not action:
        bot.send_message(chat_id, "❌ Data sesi hilang. Ulangi dari /menu.")
        return

    bot.send_message(chat_id, "⏳ Menyimpan konfigurasi Firewall Filter...", parse_mode="Markdown")
    
    params = {'chain': chain, 'action': action, 'comment': 'Custom Rule via Telegram'}
    
    if ip_target != 'all':
        params['src_address'] = ip_target
        
    if proto_port != 'all':
        parts = proto_port.split()
        params['protocol'] = parts[0]
        if len(parts) > 1:
            params['dst_port'] = parts[1]

    try:
        connection = routeros_api.RouterOsApiPool(MIKROTIK_IP, username=MIKROTIK_USER, password=MIKROTIK_PASS, plaintext_login=True)
        connection.get_api().get_resource('/ip/firewall/filter').add(**params)
        connection.disconnect()
        
        bot.send_message(chat_id, f"✅ **Firewall Filter Berhasil Dibuat!**\nChain: `{chain}`\nAction: `{action}`\nIP: `{ip_target}`\nProtocol/Port: `{proto_port}`", parse_mode="Markdown")
        user_data.pop(chat_id, None) 
    except Exception as e:
        bot.send_message(chat_id, f"❌ Gagal mengeksekusi Filter: `{e}`", parse_mode="Markdown")

# --- B. FUNGSI NAT ---
def process_nat_masq(message):
    if not is_admin(message.chat.id): return
    ip_network = message.text.strip()
    try:
        connection = routeros_api.RouterOsApiPool(MIKROTIK_IP, username=MIKROTIK_USER, password=MIKROTIK_PASS, plaintext_login=True)
        connection.get_api().get_resource('/ip/firewall/nat').add(chain='srcnat', action='masquerade', src_address=ip_network)
        connection.disconnect()
        bot.send_message(message.chat.id, f"✅ Masquerade untuk `{ip_network}` berhasil dibuat.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Gagal: `{e}`", parse_mode="Markdown")

def process_nat_dst(message):
    if not is_admin(message.chat.id): return
    chat_id = message.chat.id
    try:
        args = message.text.split()
        if len(args) != 4:
            bot.send_message(chat_id, "❌ Format salah. Harus terdiri dari 4 bagian (IP_Tujuan Port_Tujuan IP_Lokal Port_Lokal).")
            return
        dst_ip, dst_port, to_ip, to_port = args
        connection = routeros_api.RouterOsApiPool(MIKROTIK_IP, username=MIKROTIK_USER, password=MIKROTIK_PASS, plaintext_login=True)
        connection.get_api().get_resource('/ip/firewall/nat').add(
            chain='dstnat', action='dst-nat', protocol='tcp', dst_address=dst_ip, dst_port=dst_port, to_addresses=to_ip, to_ports=to_port
        )
        connection.disconnect()
        bot.send_message(chat_id, f"✅ Port Forwarding ke `{to_ip}:{to_port}` berhasil dibuat.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Gagal: `{e}`", parse_mode="Markdown")

# --- C. FUNGSI MANGLE ---
def process_mangle_ip(message):
    if not is_admin(message.chat.id): return
    chat_id = message.chat.id
    user_data[chat_id]['mangle_ip'] = message.text.strip()
    msg = bot.send_message(chat_id, "**Step 4: Ketik Nama Mark** (contoh: `koneksi_game`):", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_mangle_execute)

def process_mangle_execute(message):
    if not is_admin(message.chat.id): return
    chat_id = message.chat.id
    mark_name = message.text.strip()
    data = user_data.get(chat_id, {})
    chain = data.get('mangle_chain')
    action = data.get('mangle_action')
    ip_target = data.get('mangle_ip')
    
    mark_param = "new-connection-mark" if action == "mark-connection" else "new-packet-mark" if action == "mark-packet" else "new-routing-mark"

    try:
        connection = routeros_api.RouterOsApiPool(MIKROTIK_IP, username=MIKROTIK_USER, password=MIKROTIK_PASS, plaintext_login=True)
        params = {'chain': chain, 'action': action, mark_param: mark_name, 'passthrough': 'yes'}
        if ip_target.lower() != 'all': params['src_address'] = ip_target
        connection.get_api().get_resource('/ip/firewall/mangle').add(**params)
        connection.disconnect()
        bot.send_message(chat_id, f"✅ **Mangle Berhasil Dibuat!**", parse_mode="Markdown")
        user_data.pop(chat_id, None)
    except Exception as e:
        bot.send_message(chat_id, f"❌ Gagal mengeksekusi Mangle: `{e}`", parse_mode="Markdown")

# --- D. FUNGSI ADDRESS LIST ---
def process_address_list_name(message):
    if not is_admin(message.chat.id): return
    user_data[message.chat.id] = {'target_list': message.text.strip()}
    msg = bot.send_message(message.chat.id, f"List: `{message.text.strip()}`\n👉 Ketik **IP Address**:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_address_list_ip)

def process_address_list_ip(message):
    if not is_admin(message.chat.id): return
    chat_id = message.chat.id
    ip_address = message.text.strip()
    list_name = user_data.get(chat_id, {}).get('target_list')
    try:
        connection = routeros_api.RouterOsApiPool(MIKROTIK_IP, username=MIKROTIK_USER, password=MIKROTIK_PASS, plaintext_login=True)
        connection.get_api().get_resource('/ip/firewall/address-list').add(address=ip_address, list=list_name)
        connection.disconnect()
        bot.send_message(chat_id, f"✅ IP `{ip_address}` masuk ke list `{list_name}`.", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(chat_id, f"❌ Gagal: `{e}`", parse_mode="Markdown")

# --- JALANKAN ---
print("Bot sedang berjalan...")
bot.infinity_polling()
