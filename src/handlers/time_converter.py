"""Hijri/Gregorian date converter."""

from datetime import datetime
import pytz
import logging
from hijri_converter import convert, Hijri, Gregorian
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.utils.decorators import group_only

logger = logging.getLogger(__name__)


@group_only
async def handle_hijri_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current Hijri and Gregorian dates."""
    text = (update.message.text or "").strip()
    
    if text not in ("التاريخ الهجري", "التاريخ", "hijri date", "date"):
        return
    
    # Get current Gregorian date
    now_gregorian = Gregorian.today()
    
    # Convert to Hijri
    hijri_date = convert.Gregorian(
        now_gregorian.year,
        now_gregorian.month,
        now_gregorian.day
    ).to_hijri()
    
    # Get time
    now = datetime.now(pytz.timezone('Asia/Riyadh'))
    time_str = now.strftime("%H:%M:%S")
    day_str = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت'][now.weekday()]
    
    # Month names
    gregorian_months = [
        '', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
        'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
    ]
    
    hijri_months = [
        '', 'محرم', 'صفر', 'ربيع الأول', 'ربيع الثاني', 'جمادى الأولى', 'جمادى الآخرة',
        'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة'
    ]
    
    response = (
        f"🕌 **التاريخ الهجري:**\n"
        f"📅 {hijri_date.day} / {hijri_months[hijri_date.month]} / {hijri_date.year} هـ\n\n"
        f"📆 **التاريخ الميلادي:**\n"
        f"📅 {now_gregorian.day} / {gregorian_months[now_gregorian.month]} / {now_gregorian.year} م\n\n"
        f"📌 **اليوم:** {day_str}\n"
        f"🕐 **الوقت:** {time_str}\n"
        f"🌍 **المنطقة الزمنية:** Asia/Riyadh"
    )
    
    await update.message.reply_text(response, parse_mode="Markdown")


@group_only
async def handle_gregorian_to_hijri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert Gregorian date to Hijri."""
    text = (update.message.text or "").strip()
    
    if not text.startswith("تحويل"):
        return
    
    parts = text.replace("تحويل", "").strip().split("/")
    
    if len(parts) != 3:
        await update.message.reply_text(
            "✯ الصيغة: تحويل 15/3/2024\n"
            "(اليوم/الشهر/السنة)"
        )
        return
    
    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        
        hijri_date = convert.Gregorian(year, month, day).to_hijri()
        
        hijri_months = [
            '', 'محرم', 'صفر', 'ربيع الأول', 'ربيع الثاني', 'جمادى الأولى', 'جمادى الآخرة',
            'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة'
        ]
        
        response = (
            f"✯ التاريخ الميلادي: {day}/{month}/{year}\n"
            f"✯ يساوي بالهجري: {hijri_date.day} {hijri_months[hijri_date.month]} {hijri_date.year} هـ"
        )
        
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"✯ خطأ: {str(e)[:50]} ❌")


@group_only
async def handle_hijri_to_gregorian(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Convert Hijri date to Gregorian."""
    text = (update.message.text or "").strip()
    
    if not text.startswith("تحويل هـ"):
        return
    
    parts = text.replace("تحويل هـ", "").strip().split("/")
    
    if len(parts) != 3:
        await update.message.reply_text(
            "✯ الصيغة: تحويل هـ 15/3/1445\n"
            "(اليوم/الشهر/السنة)"
        )
        return
    
    try:
        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
        
        hijri = Hijri(year, month, day)
        gregorian_date = hijri.to_gregorian()
        
        gregorian_months = [
            '', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
            'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
        ]
        
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"✯ خطأ: {str(e)[:50]} ❌")


def register(app: Application) -> None:
    """Register time converter handlers."""
    app.add_handler(
        MessageHandler(
            filters.Regex("^(التاريخ الهجري|التاريخ|hijri date|date)$"),
            handle_hijri_date
        ),
        group=10
    )
    app.add_handler(
        MessageHandler(filters.Regex("^تحويل"), handle_gregorian_to_hijri),
        group=10
    )
    app.add_handler(
        MessageHandler(filters.Regex("^تحويل هـ"), handle_hijri_to_gregorian),
        group=10
    )
