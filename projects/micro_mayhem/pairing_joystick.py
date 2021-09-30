def begin_pairing():
  add_button_interrupt(A_BUTTON, decrement_channel)
  add_button_interrupt(B_BUTTON, increment_channel)
  add_button_interrupt(AB_BUTTON, setup)

def decrement_channel():
  RADIO_GROUP -= 1
  if RADIO_GROUP < 1:
    RADIO_GROUP = 1
    basic.show_icon(IconNames.NO)
