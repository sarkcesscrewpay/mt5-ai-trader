import shutil
import os

# Create dist/config directory
os.makedirs("dist/config", exist_ok=True)

# Copy config
shutil.copy("config/trading_config.yaml", "dist/config/")

print("Config copied to dist/config/")
print("Build complete!")
print(f"Executable: dist/MT5_Trading_Bot.exe")
print(f"Size: {os.path.getsize('dist/MT5_Trading_Bot.exe') / 1024 / 1024:.1f} MB")
