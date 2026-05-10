import os

replacements = {
    "com.lider.minebridge.networking.payload.MarketplaceRequestPayload": "com.lider.minebridge.marketplace.networking.MarketplaceRequestPayload",
    "com.lider.minebridge.networking.payload.OpenCreationMenuPayload": "com.lider.minebridge.marketplace.networking.OpenCreationMenuPayload",
    "com.lider.minebridge.networking.payload.OpenTransactionMenuPayload": "com.lider.minebridge.marketplace.networking.OpenTransactionMenuPayload",
    "com.lider.minebridge.networking.payload.CompleteTradePayload": "com.lider.minebridge.marketplace.networking.CompleteTradePayload",
    "com.lider.minebridge.networking.payload.PublishTradePayload": "com.lider.minebridge.marketplace.networking.PublishTradePayload",
    "com.lider.minebridge.networking.payload.CancelTradePayload": "com.lider.minebridge.marketplace.networking.CancelTradePayload",
    "com.lider.minebridge.networking.payload.TransactionScreenDataPayload": "com.lider.minebridge.marketplace.networking.TransactionScreenDataPayload",
    "com.lider.minebridge.networking.payload.AchievementUnlockPayload": "com.lider.minebridge.achievements.networking.AchievementUnlockPayload"
}

def refactor_files(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".java"):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = content
                    for old, new in replacements.items():
                        new_content = new_content.replace(old, new)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Refactored: {path}")
                except Exception as e:
                    print(f"Error processing {path}: {e}")

refactor_files("mod/clientmod/src")
refactor_files("mod/servermod/src")
