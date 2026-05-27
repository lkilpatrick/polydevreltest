from _gen import *  # <AUTO GENERATED>


@func_description("Say goodbye and end the conversation if and only if you've explicitly confirmed with the user that they don't need help with anything else")
def goodbye_and_hang_up(conv: Conversation):
  return {
    "utterance": "Okay. I hope you have a great rest of your day. Goodbye!",
    "hangup": True
  }