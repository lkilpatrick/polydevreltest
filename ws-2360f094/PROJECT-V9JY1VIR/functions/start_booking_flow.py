from _gen import *  # <AUTO GENERATED>


@func_description("Start the Sanctuary Cruises booking and availability flow when the caller wants to book a trip, check availability, find trip times on a specific date, or ask whether there is room for their group")
def start_booking_flow(conv: Conversation):
    conv.goto_flow("Booking Flow")
