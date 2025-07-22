# 🤖 Anuj Bot - Personal Assistant Telegram Bot

A comprehensive Telegram bot with advanced features including individual user memory, context understanding, file management, quiz generation, image doubt solving, and auto-filter capabilities.

## ✨ Features

### 🧠 Core Intelligence
- **Individual User Memory** - Remembers each user's conversation history
- **Context Understanding** - Understands user intent without explicit commands
- **Auto-Filter Capabilities** - Works like an intelligent filter system
- **Hindi-English Mixed Responses** - Natural Hinglish communication

### 📚 File Management
- **Smart File Storage** - Organizes files by type and user
- **Context-Based File Retrieval** - Suggests relevant files based on conversation
- **Channel Integration** - Can store and forward files from admin channels
- **File Search & Categorization** - Easy file discovery

### 🧠 Quiz Generation
- **PDF to Quiz Conversion** - Automatically generates quizzes from PDF content
- **Group Quiz Conducting** - Interactive group quizzes with leaderboards
- **Multiple Choice Questions** - AI-generated MCQs with explanations
- **Score Tracking** - Individual and group performance tracking

### 🖼️ Image Doubt Solving
- **OCR Text Extraction** - Reads text from images using advanced OCR
- **Handwriting-Style Solutions** - Overlays solutions that look hand-written
- **Multi-Subject Support** - Math, Physics, Chemistry, and more
- **Step-by-Step Solutions** - Detailed explanations in Hinglish

### 👥 Group Features
- **Group Quiz Management** - Conduct quizzes in groups
- **Member Tracking** - Track group member participation
- **Leaderboards** - Group and individual performance rankings
- **Admin Controls** - Group-specific settings and controls

### 🎯 Special Responses
- **Thanks Response** - Special surprise links when users say thanks
- **Best Wishes Response** - Encouraging responses for good wishes
- **Motivational Messages** - "Don't suffer in silence" encouragement

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- OpenAI API Key
- Required system packages for OCR

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd anuj_bot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install system dependencies (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-hin
sudo apt install libgl1-mesa-glx libglib2.0-0
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env file with your actual values
```

5. **Run the bot**
```bash
python bot.py
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot Token from @BotFather | Yes |
| `OPENAI_API_KEY` | OpenAI API Key for AI features | Yes |
| `BOT_USERNAME` | Bot username (without @) | No |
| `DATABASE_PATH` | SQLite database file path | No |
| `FILES_DIR` | Directory for file storage | No |
| `MAX_FILE_SIZE` | Maximum file size in MB | No |
| `ADMIN_USER_IDS` | Comma-separated admin user IDs | No |

### Bot Setup

1. **Create a Telegram Bot**
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Choose a name and username
   - Save the bot token

2. **Get OpenAI API Key**
   - Visit https://platform.openai.com/
   - Create an account and get API key
   - Add credits to your account

3. **Configure Bot Permissions**
   - Enable inline mode (optional)
   - Set bot commands using @BotFather
   - Configure privacy settings

## 📖 Usage

### Basic Commands

- `/start` - Initialize bot and show welcome message
- `/help` - Show help menu with all features
- `/quiz` - Generate quiz from PDF
- `/notes` - Search and get notes/files
- `/memory` - View conversation history
- `/groupquiz` - Start group quiz (in groups)
- `/leaderboard` - View group leaderboard (in groups)

### Natural Language Usage

The bot understands natural language without commands:

- **File Requests**: "send me math notes", "physics files chahiye"
- **Quiz Requests**: "make quiz from this PDF", "test me on chemistry"
- **Doubt Solving**: Send image with math problem, "solve this equation"
- **General Chat**: "thanks", "best wishes", casual conversation

### File Management

1. **Upload Files**: Send PDF, images, or documents
2. **Auto-Categorization**: Files are automatically categorized
3. **Smart Retrieval**: Ask for files using natural language
4. **Search**: Files are searchable by name, content, or tags

### Quiz Features

1. **PDF Upload**: Send PDF to generate quiz
2. **Auto-Generation**: AI creates relevant questions
3. **Group Quizzes**: Interactive group quiz sessions
4. **Performance Tracking**: Individual and group statistics

### Image Doubt Solving

1. **Send Image**: Upload image with math/science problem
2. **OCR Processing**: Text is extracted from image
3. **AI Analysis**: Problem is analyzed and solved
4. **Handwritten Solution**: Solution overlaid on original image

## 🏗️ Architecture

### Project Structure
```
anuj_bot/
├── bot.py                 # Main bot file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── config/               # Configuration files
│   ├── __init__.py
│   └── settings.py       # Bot settings and configuration
├── database/             # Database management
│   ├── __init__.py
│   └── db_manager.py     # Database operations
├── utils/                # Utility modules
│   ├── __init__.py
│   ├── file_manager.py   # File management
│   ├── quiz_generator.py # Quiz generation
│   ├── image_solver.py   # Image processing and solving
│   ├── context_manager.py # Context understanding
│   └── group_manager.py  # Group management
├── files/                # File storage directory
├── logs/                 # Log files
└── static/               # Static assets
```

### Database Schema

The bot uses SQLite with the following main tables:
- `users` - User information and preferences
- `conversations` - Message history for memory
- `files` - File metadata and storage info
- `quizzes` - Generated quiz data
- `quiz_attempts` - Quiz performance tracking
- `user_context` - User context and state
- `groups` - Group information
- `group_members` - Group membership

### Key Components

1. **DatabaseManager** - Handles all database operations
2. **FileManager** - Manages file storage and retrieval
3. **QuizGenerator** - Creates quizzes from PDF content
4. **ImageSolver** - Processes images and generates solutions
5. **ContextManager** - Understands user context and intent
6. **GroupManager** - Handles group features and quizzes

## 🔧 Development

### Adding New Features

1. **Create utility module** in `utils/` directory
2. **Update database schema** if needed in `db_manager.py`
3. **Add handlers** in main `bot.py` file
4. **Update configuration** in `config/settings.py`
5. **Test thoroughly** before deployment

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add comprehensive docstrings
- Handle exceptions gracefully
- Log important events

### Testing

```bash
# Run basic tests
python -m pytest tests/

# Test specific components
python -c "from utils.quiz_generator import QuizGenerator; qg = QuizGenerator(); print('Quiz generator working!')"
```

## 🚀 Deployment

### Local Development
```bash
python bot.py
```

### Production Deployment

1. **Using systemd (Linux)**
```bash
# Create service file
sudo nano /etc/systemd/system/anuj-bot.service

# Add service configuration
[Unit]
Description=Anuj Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/anuj_bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl enable anuj-bot
sudo systemctl start anuj-bot
```

2. **Using Docker**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-hin \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY . .
CMD ["python", "bot.py"]
```

3. **Using PM2**
```bash
npm install -g pm2
pm2 start bot.py --name anuj-bot --interpreter python3
pm2 save
pm2 startup
```

### Environment Setup

1. **Production Environment Variables**
```bash
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
export DATABASE_PATH=/var/lib/anuj-bot/anuj_bot.db
```

2. **Security Considerations**
- Keep bot token secure
- Use environment variables for sensitive data
- Regular database backups
- Monitor logs for errors
- Set up proper file permissions

## 📊 Monitoring

### Logs
- Bot activities logged to `logs/anuj_bot.log`
- Error tracking and debugging information
- User interaction statistics

### Database Maintenance
```bash
# Backup database
cp database/anuj_bot.db database/backup_$(date +%Y%m%d).db

# Clean old conversation data (optional)
python -c "from database.db_manager import DatabaseManager; db = DatabaseManager(); db.cleanup_old_data(30)"
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review logs for error messages

## 🙏 Acknowledgments

- OpenAI for GPT API
- python-telegram-bot library
- OCR libraries (Tesseract, EasyOCR)
- All contributors and users

---

**Made with ❤️ for Indian students and educators**

*"Don't suffer in silence - ask Anuj!"* 😊

