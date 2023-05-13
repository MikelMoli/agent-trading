def get_position_name(position: int) -> str:
    if position == 0:
        return "LONG"
    elif position == 1:
        return "SHORT"
    elif position == 2:
        return "FLAT"
    
def get_action_name(action: int) -> str:
    if action == 0:
        return "BUY"
    elif action == 1:
        return "SELL"
    elif action == 2:
        return "HOLD"