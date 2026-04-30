import pypresence

RPC_CLIENT_ID = "120000000000000000"  # Placeholder Client ID
rpc = None

def init_discord_rpc():
    global rpc
    try:
        if rpc is None:
            rpc = pypresence.Presence(RPC_CLIENT_ID)
            rpc.connect()
            rpc.update(state="In Launcher", details="Ready to Play", large_image="minecraft")
    except:
        pass

def update_discord_rpc(state, details):
    global rpc
    try:
        if rpc:
            rpc.update(state=state, details=details, large_image="minecraft")
    except:
        pass