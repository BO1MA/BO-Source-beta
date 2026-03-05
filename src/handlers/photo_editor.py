"""Photo text editor - add text to images."""

import logging
import io
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest

from src.utils.decorators import group_only

logger = logging.getLogger(__name__)


@group_only
async def handle_photo_text_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle photo text edit command."""
    text = (update.message.text or "").strip()
    
    # Check if replying to a photo
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "✯ الرجاء الرد على صورة بـ أي نص\n"
            "المثال: رد على الصورة ثم ارسل: كتابة على الصورة|النص المراد كتابته"
        )
        return
    
    reply_msg = update.message.reply_to_message
    
    # Check if reply is to a photo
    if not reply_msg.photo:
        await update.message.reply_text("✯ الرجاء الرد على صورة فقط")
        return
    
    # Extract text to write
    if not text or "|" not in text:
        await update.message.reply_text(
            "✯ الصيغة: كتابة|النص المراد كتابته\n"
            "المثال: كتابة|مرحبا"
        )
        return
    
    write_text = text.split("|", 1)[1].strip()
    
    if not write_text:
        await update.message.reply_text("✯ الرجاء إدخال النص")
        return
    
    msg = await update.message.reply_text("✯ جاري تحرير الصورة... ⏳")
    
    try:
        # Download photo
        photo_file = await reply_msg.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Open image
        img = Image.open(io.BytesIO(photo_bytes))
        
        # Add text to image
        img_with_text = add_text_to_image(img, write_text)
        
        # Save to bytes
        output = io.BytesIO()
        img_with_text.save(output, format="PNG")
        output.seek(0)
        
        # Send edited photo
        await update.message.reply_photo(
            photo=output,
            caption="✯ تم إضافة النص بنجاح 🎨"
        )
        
        await msg.delete()
        
    except BadRequest as e:
        logger.error(f"Photo download error: {e}")
        await msg.edit_text("✯ خطأ في تحميل الصورة ❌")
    except Exception as e:
        logger.error(f"Photo text error: {e}")
        await msg.edit_text(f"✯ خطأ: {str(e)[:50]} ❌")


def add_text_to_image(img: Image.Image, text: str) -> Image.Image:
    """Add text to image."""
    # Create a copy
    img_copy = img.copy()
    
    # Get drawing context
    draw = ImageDraw.Draw(img_copy)
    
    # Try to use a nice font, fallback to default
    try:
        # Try to load Arabic font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", 30)
        except:
            font = ImageFont.load_default()
    
    # Get image dimensions
    width, height = img_copy.size
    
    # Calculate text position (bottom center)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = height - text_height - 20
    
    # Add white background for text
    padding = 10
    draw.rectangle(
        [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
        fill=(255, 255, 255, 200)
    )
    
    # Draw text
    draw.text((x, y), text, fill=(0, 0, 0), font=font)
    
    return img_copy


@group_only
async def handle_photo_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Apply filters to photos."""
    text = (update.message.text or "").strip()
    
    if not text.startswith("فلتر"):
        return
    
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        await update.message.reply_text("✯ الرجاء الرد على صورة")
        return
    
    filter_type = text.replace("فلتر", "").strip()
    
    if not filter_type:
        await update.message.reply_text(
            "✯ الفلاتر المتاحة:\n"
            "• فلتر رمادي\n"
            "• فلتر سيبيا\n"
            "• فلتر معكوس"
        )
        return
    
    msg = await update.message.reply_text("✯ جاري تطبيق الفلتر... ⏳")
    
    try:
        # Download photo
        reply_msg = update.message.reply_to_message
        photo_file = await reply_msg.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Open image
        img = Image.open(io.BytesIO(photo_bytes))
        
        # Apply filter
        if "رمادي" in filter_type:
            filtered = img.convert("L")
        elif "سيبيا" in filter_type:
            filtered = apply_sepia(img)
        elif "معكوس" in filter_type:
            filtered = apply_invert(img)
        else:
            await msg.edit_text("✯ فلتر غير معروف")
            return
        
        # Save to bytes
        output = io.BytesIO()
        filtered.save(output, format="PNG")
        output.seek(0)
        
        # Send filtered photo
        await update.message.reply_photo(
            photo=output,
            caption=f"✯ تم تطبيق فلتر {filter_type} 🎨"
        )
        
        await msg.delete()
        
    except Exception as e:
        logger.error(f"Filter error: {e}")
        await msg.edit_text(f"✯ خطأ: {str(e)[:50]} ❌")


def apply_sepia(img: Image.Image) -> Image.Image:
    """Apply sepia tone filter."""
    img = img.convert("RGB")
    pixels = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            tr = int(0.393 * r + 0.769 * g + 0.189 * b)
            tg = int(0.349 * r + 0.686 * g + 0.168 * b)
            tb = int(0.272 * r + 0.534 * g + 0.131 * b)
            
            pixels[x, y] = (min(255, tr), min(255, tg), min(255, tb))
    
    return img


def apply_invert(img: Image.Image) -> Image.Image:
    """Apply invert colors filter."""
    img = img.convert("RGB")
    inverted = Image.new("RGB", img.size)
    pixels = img.load()
    inv_pixels = inverted.load()
    
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            inv_pixels[x, y] = (255 - r, 255 - g, 255 - b)
    
    return inverted


def register(app: Application) -> None:
    """Register photo editor handlers."""
    app.add_handler(
        MessageHandler(filters.Regex("^كتابة"), handle_photo_text_command),
        group=10
    )
    app.add_handler(
        MessageHandler(filters.Regex("^فلتر"), handle_photo_filter),
        group=10
    )
