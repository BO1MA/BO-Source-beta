ITEMS_DATABASE = {
    "normal": {"buy_margin": 1.0, "sell_limit": 0.9, "items": ["old_phone", "cheap_watch"]},
    "rare": {"buy_margin": 2.0, "sell_limit": 5.0, "items": ["antique_house", "monalisa", "ferrari"]},
    "epic": {"buy_margin": 3.0, "sell_limit": 10.0, "items": ["private_island", "spaceship"]},
}

def get_item_rarity(item_name: str) -> str:
    for rarity, data in ITEMS_DATABASE.items():
        if item_name in data["items"]:
            return rarity
    return "normal"
