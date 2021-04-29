straight_channel = 0
turn_channel = 0

def on_received_value(name, value):
    global straight_channel
    global turn_channel
    if name == 'straight':
        straight_channel = value
    else if name == 'turn':
        turn_channel = value
