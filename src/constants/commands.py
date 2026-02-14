"""
Command definitions mapping Arabic text commands to handler keys.
Based on bian_commands.txt and bian.lua command routing.
"""
from __future__ import annotations


# Arabic commands → handler function key
COMMANDS: dict[str, list[str]] = {
    # ── Start ──
    "start": ["/start", "ستارت"],

    # ── Tag All ──
    "tag_all": ["all", "@all", "الكل"],

    # ── Info ──
    "get_id": ["Id", "ايدي"],
    "my_name": ["اسمي"],
    "bio": ["البايو"],
    "bot_info": ["البوت"],
    "group_info": ["الجروب"],
    "link": ["الرابط"],
    "admin_list": ["الادمنيه", "ادمنيه الجروب"],
    "server_info": ["السيرفر"],
    "stats": ["الاحصائيات"],
    "developer_info": ["المبرمج"],
    "source": ["السورس"],

    # ── User Info (NEW) ──
    "my_rank": ["رتبتي"],
    "my_messages": ["رسائلي"],
    "my_username": ["معرفي", "يوزري"],
    "my_title": ["لقبي"],
    "my_photo": ["صورتي"],
    "who_am_i": ["انا مين"],
    "my_bio": ["نبذتي", "سيفي"],
    "my_warnings": ["تحذيراتي"],
    "all_ranks": ["الرتب"],
    "member_count": ["عدد الاعضاء"],
    "group_name": ["اسم الجروب"],
    "group_desc": ["وصف الجروب"],

    # ── Role Listing ──
    "list_developers": ["المطورين"],
    "list_secondary_devs": ["المطورين الثانويين"],
    "list_owners": ["المالكين", "المالك"],
    "list_creators": ["المنشئين", "المنشئ"],
    "list_managers": ["المدراء"],
    "list_admins": ["الادمنية"],
    "list_vips": ["المميزين"],
    "list_banned": ["المحظورين"],
    "list_global_banned": ["المحظورين عام"],
    "list_muted": ["المكتومين"],
    "list_global_muted": ["المكتومين عام"],

    # ── Role Assignment (reply-based) ──
    "promote_secondary_dev": ["مطور ثانوي"],
    "promote_assistant": ["مساعد"],
    "promote_developer": ["مطور"],
    "promote_owner": ["مالك"],
    "promote_main_creator": ["منشئ اساسي"],
    "promote_creator": ["منشئ"],
    "promote_manager": ["مدير"],
    "promote_admin": ["ادمن"],
    "promote_vip": ["مميز"],
    "demote": ["تنزيل", "عزل"],
    "demote_all": ["تنزيل الكل"],

    # ── Broadcast ──
    "broadcast": ["اذاعه"],
    "broadcast_pin": ["اذاعه بالتثبيت"],
    "broadcast_forward": ["اذاعه بالتوجيه"],
    "broadcast_private": ["اذاعه خاص"],
    "broadcast_forward_private": ["اذاعه بالتوجيه خاص"],
    "broadcast_groups": ["اذاعه للمجموعات"],

    # ── Moderation ──
    "ban": ["حظر"],
    "unban": ["الغاء الحظر", "الغاء حظر"],
    "global_ban": ["حظر عام"],
    "global_unban": ["الغاء حظر عام"],
    "mute": ["كتم", "منع"],
    "unmute": ["الغاء كتم", "الغاء منع"],
    "global_mute": ["كتم عام"],
    "global_unmute": ["الغاء كتم عام"],
    "kick": ["طرد"],
    "kick_self": ["اطردني"],
    "warn": ["تحذير"],
    "unwarn": ["الغاء تحذير"],
    "delete_msg": ["حذف"],

    # ── Lock / Unlock ──
    "lock": ["قفل"],
    "unlock": ["فتح"],

    # ── Settings Toggle ──
    "enable_games": ["تفعيل الالعاب"],
    "disable_games": ["تعطيل الالعاب"],
    "enable_tag": ["تفعيل التاغ"],
    "disable_tag": ["تعطيل التاغ"],
    "enable_broadcast": ["تفعيل الاذاعه"],
    "disable_broadcast": ["تعطيل الاذاعه"],
    "enable_force_subscribe": ["تفعيل الاشتراك الاجباري"],
    "disable_force_subscribe": ["تعطيل الاشتراك الاجباري"],
    "enable_farewell": ["تفعيل المغادره"],
    "disable_farewell": ["تعطيل المغادره"],
    "enable_welcome": ["تفعيل الترحيب"],
    "disable_welcome": ["تعطيل الترحيب"],
    "enable_protection": ["تفعيل الحمايه"],
    "disable_protection": ["تعطيل الحمايه"],

    # ── Force Subscribe ──
    "force_subscribe_info": ["الاشتراك الاجباري"],

    # ── Custom Commands ──
    "add_command": ["اضف امر"],
    "add_global_command": ["اضف امر عام"],
    "add_reply": ["اضف رد"],
    "add_global_reply": ["اضف رد عام"],
    "delete_command": ["الغاء الامر"],
    "list_commands": ["الاوامر المضافه"],
    "list_global_commands": ["الاوامر المضافه العامه"],

    # ── Welcome / Rules ──
    "set_welcome": ["الترحيب"],
    "set_rules": ["القوانين"],

    # ── Pin ──
    "pin": ["تثبيت"],
    "unpin": ["الغاء التثبيت"],
    "unpin_all": ["الغاء تثبيت الكل"],

    # ── Protection / Settings Page ──
    "protection_settings": ["اعدادات الحمايه", "الحمايه"],
    "settings": ["الاعدادات"],

    # ── Games (12 games) ──
    "games_menu": ["الالعاب"],
    "emoji_game": ["السمايلات", "السمايل"],
    "guess_game": ["تخمين"],
    "fastest": ["الاسرع", "ترتيب"],
    "letters_game": ["الحروف"],
    "riddle_game": ["حزوره", "الحزوره"],
    "meaning_game": ["معاني", "المعاني"],
    "ring_game": ["محيبس", "المحيبس"],
    "different_game": ["المختلف"],
    "math_game": ["رياضيات"],
    "english_game": ["انكليزي"],
    "proverb_game": ["امثله", "الامثله"],
    "scramble_game": ["كلمات", "الكلمات"],

    # ── Fun ──
    "insult": ["اشتم", "اشتمو"],
    "reverse_text": ["العكس"],
    "wisdom": ["حكمه"],
    "joke": ["نكته"],
    "poetry": ["قصيده", "شعر"],
    "choose": ["خيرني"],
    "decorate": ["زخرفه"],
    "beauty_pct": ["نسبه جمالي", "نسبة جمالي", "جمالي"],
    "love_pct": ["نسبه حب", "نسبة حب"],
    "hate_pct": ["نسبه كره", "نسبة كره"],
    "tweet": ["تويت"],
    "advice": ["نصح", "نصيحه"],
    "flags": ["اعلام", "دول"],
    "flag": ["علم"],
    "say": ["قول"],
    "who_random": ["مين"],
    "time": ["الوقت", "الساعه"],

    # ── Greetings ──
    "greeting": ["السلام عليكم", "صباح الخير", "مساء الخير", "مرحبا", "الحمد لله",
                  "هلا", "شلونكم", "تصبحون على خير"],

    # ── YouTube ──
    "youtube": ["بحث يوتيوب", "يوتيوب"],

    # ── Bot Commands ──
    "main_menu": ["القائمه", "الاوامر"],

    # ── Group Management (NEW) ──
    "activate": ["تفعيل"],
    "bot_leave": ["بوت غادر"],
    "set_title": ["ضع اسم"],
    "set_description": ["ضع وصف"],
    "set_photo": ["تغيير صورة الجروب", "صورة الجروب"],
    "detect_bots": ["كشف البوتات"],
    "demote_all_cmd": ["تنزيل الكل"],

    # ── Developer / Sudo (NEW) ──
    "group_count": ["عدد الجروبات"],
    "user_count": ["عدد المستخدمين"],
    "group_list": ["قائمة الجروبات"],
}


# ── Lock Features (from GetSetieng in bian.lua) ──
LOCK_FEATURES: dict[str, str] = {
    "photo": "الصور",
    "video": "الفيديو",
    "sticker": "الملصقات",
    "gif": "الصور المتحركه",
    "animation": "الصور المتحركه",
    "document": "الملفات",
    "voice": "الرسائل الصوتيه",
    "video_note": "الرسائل المرئيه",
    "audio": "الصوتيات",
    "link": "الروابط",
    "forward": "التوجيه",
    "inline": "الازرار",
    "hashtag": "الهاشتاق",
    "contact": "جهات الاتصال",
    "bot": "البوتات",
    "command": "الاوامر",
    "spam": "السبام",
    "markdown": "الماركداون",
    "edit": "التعديل",
    "join": "الانضمام",
    "add_member": "اضافة اعضاء",
    "arabic_only": "العربي فقط",
    "english_only": "الانجليزي فقط",
    "flood": "الفلود",
    "long_message": "الرسائل الطويله",
    "location": "الموقع",
    "game": "الالعاب",
    "poll": "التصويت",
    "dice": "النرد",
    "profanity": "الشتايم",
    "persian": "الفارسي",
}

# Lock punishment types (from Lua)
LOCK_PUNISHMENTS = {
    "delete": "حذف",     # Just delete the message
    "warn": "تحذير",     # Warn the user
    "kick": "طرد",       # Kick the user
    "mute": "كتم",       # Mute the user
    "ban": "حظر",        # Ban the user
}


def find_command_key(text: str) -> str | None:
    """Given user text, return the matching command key or None."""
    text_stripped = text.strip()
    for key, triggers in COMMANDS.items():
        for trigger in triggers:
            if text_stripped == trigger or text_stripped.startswith(trigger + " "):
                return key
    return None
