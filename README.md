# Assignment Tracker

A comprehensive assignment tracking application with AI integration, built with FastAPI backend, React frontend, and MCP server architecture.

## 🚀 Features

- **📚 Class Management**: Organize assignments by classes/subjects
- **📅 Calendar View**: Visual calendar interface for due dates
- **⚡ Status Tracking**: Track assignments as not started, in progress, or completed
- **🤖 AI Integration**: Parse syllabi and generate assignments using Groq AI
- **📊 Dashboard**: Overview of your progress and upcoming assignments
- **🎨 Beautiful UI**: Modern, responsive design with smooth animations

## ⚡ Quick Start

### Option 1: Docker (Recommended)
The easiest way to run the application with consistent environment:

```bash
# Start the application
docker-compose up --build

# Or run in background
docker-compose up -d --build

# Stop the application
docker-compose down
```

**Access the app:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8001`
- API Docs: `http://localhost:8001/docs`

📖 See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed Docker instructions.

### Option 2: Native Setup (Legacy)
For local development without Docker:

**Windows:**
```bash
# Double-click or run:
start_app.bat
```

**To stop the application:**
- Use the red "Shutdown" button in the app's navigation bar, OR
- Run `stop_app.bat`

### What happens during startup:
1. 🔧 Backend server starts on `http://localhost:8001`
2. 🌐 Frontend server starts on `http://localhost:3000`
3. 🚀 App opens automatically in your browser
4. ✨ Ready to use!

## 🏗️ Architecture

### Backend (FastAPI)
- RESTful API with SQLAlchemy ORM
- SQLite database for local storage
- AI service integration with Groq
- CORS enabled for frontend communication

### Frontend (React + Vite)
- Modern React with hooks and functional components
- Tailwind CSS for styling
- Framer Motion for animations
- React Router for navigation
- Axios for API communication

### MCP Server
- Model Context Protocol server for assignment management
- Tools for creating classes and assignments
- Calendar view generation
- Status update operations

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy .env file and update with your settings
# Add your Groq API key to GROQ_API_KEY
```

5. Run the FastAPI server:
```bash
python main.py
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### MCP Server Setup

1. Navigate to the MCP server directory:
```bash
cd mcp_server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the MCP server:
```bash
python server.py
```

## 📖 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

### Main Endpoints

- `GET /api/classes` - Get all classes
- `POST /api/classes` - Create a new class
- `GET /api/assignments` - Get assignments with filtering
- `POST /api/assignments` - Create a new assignment
- `PATCH /api/assignments/{id}/status` - Update assignment status
- `GET /api/assignments/calendar` - Get calendar view
- `POST /api/ai/parse-syllabus` - Parse syllabus with AI
- `POST /api/ai/generate-assignments` - Generate assignments with AI

## 🤖 AI Features

### Syllabus Parsing
Paste any syllabus text and the AI will automatically:
- Extract course information
- Identify assignments and due dates
- Create class and assignment records
- Set appropriate priorities and time estimates

### Assignment Generation
Provide a natural language prompt like:
- "Create 3 progressive programming assignments for learning React.js"
- "Generate study tasks for preparing for a calculus midterm exam"
- "Design weekly lab assignments for an organic chemistry course"

## 🎨 UI Components

### Dashboard
- Assignment statistics and overview
- Upcoming assignments
- Quick actions for common tasks

### Calendar View
- Monthly calendar with assignment visualization
- Click dates to view assignments
- Status-based color coding

### Classes Page
- Create and manage classes
- View assignments by class
- Class-specific assignment creation

### AI Assistant
- Syllabus parsing interface
- Assignment generation tools
- AI status monitoring

## 🔧 Configuration

### Environment Variables

Backend (`.env`):
```env
GROQ_API_KEY=your_groq_api_key_here
DATABASE_URL=sqlite:///./assignments.db
DEBUG=True
FRONTEND_URL=http://localhost:3000
```

### Database Schema

- **Classes**: Store course information with colors and descriptions
- **Assignments**: Track assignments with status, priority, due dates, and time estimates
- **Relationships**: Assignments belong to classes with foreign key constraints

## 🚀 Deployment

### Backend Deployment
1. Set up a production WSGI server (e.g., Gunicorn)
2. Configure environment variables for production
3. Set up a production database (PostgreSQL recommended)

### Frontend Deployment
1. Build the production bundle:
```bash
npm run build
```
2. Serve the `dist` folder with a web server (Nginx, Apache, etc.)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙋‍♂️ Support

For questions or issues:
1. Check the API documentation at `/docs`
2. Review the console logs for frontend issues
3. Ensure all dependencies are properly installed
4. Verify environment variables are set correctly

## 🎯 Future Enhancements

- [ ] Email notifications for due dates
- [ ] Mobile app version
- [ ] Team collaboration features
- [ ] Integration with Google Calendar
- [ ] Advanced AI features (assignment difficulty prediction)
- [ ] Export/import functionality
- [ ] Dark mode support
- [ ] Offline functionality with PWA

---

Built with ❤️ using FastAPI, React, and AI integration.
