# JARVIS Autostart Feature

This feature allows your JARVIS system to start automatically whenever your PC boots up, so it's always running and ready for your commands.

## Setup Instructions

1. **First-time preparation**:
   - Make sure you have one of these server files in your directory:
     - `minimal_server.py` (preferred and recommended)
     - `jarvis_server.py`
     - `simple_server.py`
     - `server.py`
   - A `requirements.txt` file has been created for you

2. **One-time setup**: Run `create_jarvis_startup.bat` by double-clicking it
   - This will create a shortcut in your Windows Startup folder
   - JARVIS will now start automatically each time you log into Windows

3. **If you need to remove JARVIS from startup**: 
   - Run `remove_jarvis_startup.bat`
   - This will remove JARVIS from the Windows startup sequence

## How It Works

The autostart system will:
1. Find the best available server file (prioritizing minimal_server.py)
2. Install all required dependencies
3. Create a default .env file if one doesn't exist
4. Start the server in invisible background mode

The scripts are smart enough to:
- Use minimal_server.py if available (strongly recommended)
- Check for other server files as fallbacks
- Use requirements.txt if available, otherwise install packages directly
- Test connections on both port 8000 and 8080

## Components

- `jarvis_autostart.bat`: The actual script that starts JARVIS in background mode
- `create_jarvis_startup.bat`: Adds JARVIS to Windows startup
- `remove_jarvis_startup.bat`: Removes JARVIS from Windows startup
- `requirements.txt`: Lists all required Python packages
- `.env`: Optional configuration file (will be created if missing)

## Log Files

- `jarvis_last_start.log`: Created each time JARVIS starts successfully
- `jarvis_error.log`: Created if there's a startup problem

## Troubleshooting

If JARVIS isn't starting automatically:

1. Check the log files to see if there were any errors
2. Run `jarvis_autostart.bat` manually to see detailed outputs
3. Make sure you have minimal_server.py or one of the alternative server files
4. Verify the shortcut exists in `C:\Users\[YourUsername]\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`

If you need to stop JARVIS completely, open Task Manager and end any Python/pythonw processes related to JARVIS. 