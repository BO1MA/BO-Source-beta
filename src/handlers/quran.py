"""Quran search and tafsir handler."""

import logging
import httpx
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from src.utils.decorators import group_only

logger = logging.getLogger(__name__)

QURAN_API = "https://api.alquran.cloud/v1"


@group_only
async def handle_quran_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Quran search commands."""
    text = (update.message.text or "").strip()
    
    # Extract search type and query
    search_type = None
    query = None
    
    if text.startswith("ميسر "):
        search_type = "tafsir_muyassar"
        query = text[5:].strip()
    elif text.startswith("جلالين "):
        search_type = "tafsir_jalalayn"
        query = text[7:].strip()
    elif text.startswith("بحث قرآن "):
        search_type = "search"
        query = text[9:].strip()
    else:
        return
    
    if not query:
        await update.message.reply_text("✯ الرجاء إدخال النص للبحث عنه 📖")
        return
    
    msg = await update.message.reply_text("✯ جاري البحث... ⏳")
    
    try:
        if search_type == "search":
            results = await search_quran(query)
        elif search_type == "tafsir_muyassar":
            results = await get_tafsir(query, "muyassar")
        else:
            results = await get_tafsir(query, "jalalayn")
        
        if not results:
            await msg.edit_text("✯ لم يتم العثور على نتائج ❌")
            return
        
        # Send first 5 results
        response = "✯ نتائج البحث:\n\n"
        for i, result in enumerate(results[:5], 1):
            response += f"{i}. {result}\n\n"
        
        await msg.edit_text(response)
        
    except Exception as e:
        logger.error(f"Quran search error: {e}")
        await msg.edit_text("✯ حدث خطأ في البحث ❌")


async def search_quran(query: str) -> list:
    """Search Quran by text."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{QURAN_API}/surah",
                params={"language": "ar"}
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            results = []
            
            # Simple search through surahs
            for surah in data.get("data", []):
                if query.lower() in surah.get("name", "").lower():
                    results.append(
                        f"سورة {surah.get('name')} - عدد الآيات: {surah.get('numberOfAyahs')}"
                    )
            
            return results
            
    except Exception as e:
        logger.error(f"Quran API error: {e}")
        return []


async def get_tafsir(query: str, tafsir_type: str) -> list:
    """Get tafsir interpretation for a Quranic verse."""
    try:
        # Find the surah/ayah first
        async with httpx.AsyncClient(timeout=10) as client:
            # Search for the query in the Quran
            response = await client.get(
                f"{QURAN_API}/search",
                params={"query": query, "language": "ar"}
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            matches = data.get("data", {}).get("matches", [])
            
            if not matches:
                return []
            
            results = []
            
            # Get tafsir for first 3 matches
            for match in matches[:3]:
                surah_num = match.get("surah", 1)
                ayah_num = match.get("ayah", 1)
                
                tafsir_response = await client.get(
                    f"{QURAN_API}/ayah/{surah_num}:{ayah_num}/tafsirs"
                )
                
                if tafsir_response.status_code == 200:
                    tafsir_data = tafsir_response.json()
                    tafsirs = tafsir_data.get("data", [])
                    
                    if tafsirs:
                        first_tafsir = tafsirs[0]
                        results.append(
                            f"السورة {surah_num} الآية {ayah_num}:\n"
                            f"{first_tafsir.get('text', 'لا يوجد تفسير')[:200]}..."
                        )
            
            return results
            
    except Exception as e:
        logger.error(f"Tafsir error: {e}")
        return []


def register(app: Application) -> None:
    """Register Quran handler."""
    app.add_handler(
        MessageHandler(
            filters.Regex("^(ميسر|جلالين|بحث قرآن) "),
            handle_quran_search
        ),
        group=10
    )
