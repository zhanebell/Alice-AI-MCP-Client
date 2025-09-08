# Alice AI Assignment Tracker - Quick Start Guide

## 🚀 One-Click Startup

To start the entire Alice AI Assignment Tracker application, simply double-click one of these files:

### Windows Users:
- **`start_app.bat`** - Windows Batch script (recommended for most users)
- **`start_app.ps1`** - PowerShell script (if you prefer PowerShell)

### What happens when you run the startup script:
1. **Backend Server** starts on `http://localhost:8001` (FastAPI with AI services)
2. **Frontend Server** starts on `http://localhost:3000` (React with Vite)
3. **Browser** automatically opens to `http://localhost:3000`
4. **Ready to use!** 🎉

## 🛑 Stopping the Application

### Option 1: Use the stop script
- Double-click **`stop_app.bat`** to cleanly shut down all services

### Option 2: Manual shutdown
- Close the Backend and Frontend terminal windows
- Or press `Ctrl+C` in each terminal window

## 💾 Database Persistence

**Your data is safe!** The SQLite database (`backend/assignments.db`) is stored as a file on your computer. This means:
- ✅ All your assignments, classes, and data persist between sessions
- ✅ You can close the app and restart it anytime without losing data
- ✅ Data is stored locally on your computer (no cloud dependency)

## 🔧 What Each Service Does

### Backend (Port 8001)
- **FastAPI server** with REST API endpoints
- **SQLite database** for storing assignments and classes
- **AI service** integration with Groq for intelligent assignment generation
- **Health checks** and status monitoring

### Frontend (Port 3000)
- **React application** with modern UI components
- **Vite development server** with hot module replacement
- **AI Assistant page** for syllabus parsing and assignment generation
- **Dashboard, Calendar, and Classes** management pages

## 🤖 AI Features

The app includes powerful AI capabilities:
- **Syllabus Parsing**: Upload course syllabi and automatically extract assignments
- **Assignment Generation**: Use natural language prompts to create assignments
- **Smart Scheduling**: AI suggests realistic due dates and time estimates
- **Class Management**: Automatically organizes assignments by class

## 🆘 Troubleshooting

### If the startup script fails:
1. Make sure you're running it from the `Alice-AI-MCP-Client` directory
2. Ensure Python and Node.js are installed on your system
3. Check that ports 3000 and 8001 are not in use by other applications

### If the app doesn't open:
- Wait a few seconds for services to start up
- Manually navigate to `http://localhost:3000` in your browser

### If you see errors:
- Check the terminal windows for error messages
- Ensure your `.env` file contains a valid `GROQ_API_KEY`
- Try running `stop_app.bat` and then `start_app.bat` again

## 📁 Project Structure

```
Alice-AI-MCP-Client/
├── start_app.bat          # 🚀 One-click startup (Windows)
├── start_app.ps1          # 🚀 One-click startup (PowerShell)
├── stop_app.bat           # 🛑 Clean shutdown
├── backend/               # FastAPI server
│   ├── main.py           # Server entry point
│   ├── assignments.db    # 💾 Your persistent database
│   └── app/              # Application code
├── frontend/             # React application
│   ├── src/              # Source code
│   └── package.json      # Dependencies
└── .env                  # Environment variables (GROQ_API_KEY)
```

## 🎯 Quick Start Checklist

1. ✅ Clone/download the project
2. ✅ Add your `GROQ_API_KEY` to the `.env` file
3. ✅ Double-click `start_app.bat`
4. ✅ Wait for browser to open automatically
5. ✅ Start managing your assignments with AI! 🎉

---

**Need help?** Check the terminal windows for detailed error messages or refer to the main project documentation.
