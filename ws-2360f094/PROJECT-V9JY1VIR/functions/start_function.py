from _gen import *  # <AUTO GENERATED>


def start_function(conv: Conversation):
    """Initialize conversation state at call start."""
    conv.state.booking_confirmed = False
    conv.state.booking_url = "https://fareharbor.com/embeds/book/sanctuarycruises/?flow=1127712&full-items=yes"
    conv.state.fareharbor_result = None
