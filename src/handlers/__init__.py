"""
Handler registration — imports all handler modules and provides
a single register_all_handlers() function for bot.py to call.
"""
from telegram.ext import Application

from . import start, admin, moderation, broadcast, games, tag, locks, permissions, youtube, fun, dm_relay


def register_all_handlers(app: Application) -> None:
    """Register every handler module with the Application."""
    start.register(app)
    admin.register(app)
    moderation.register(app)
    broadcast.register(app)
    games.register(app)
    tag.register(app)
    locks.register(app)
    permissions.register(app)
    youtube.register(app)
    fun.register(app)
    dm_relay.register(app)
