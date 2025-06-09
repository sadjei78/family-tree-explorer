# 🌳 Family Tree Explorer

A modern, interactive web application for exploring family genealogy data from GEDCOM files. Built with Flask and featuring relationship calculations, generation mapping, and a beautiful responsive interface.

## 🌟 Features

- **📊 Interactive Family Tree Navigation** - Explore relationships with clickable family connections
- **🔍 Smart Search** - Find family members quickly with fuzzy search
- **👥 Relationship Calculator** - Discover how people are related (cousins, grandparents, etc.)
- **📈 Generation Mapping** - See family generations clearly labeled
- **📝 Family Submissions** - Allow family members to submit corrections and additions
- **💬 Feedback System** - Collect feedback and questions from users
- **🔐 Secure Admin Panel** - Password-protected administration interface
- **📱 Responsive Design** - Works beautifully on desktop, tablet, and mobile

## 🚀 Live Demo

**[View Live Demo](https://your-render-url.onrender.com)** *(Coming soon)*

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Data**: GEDCOM file parsing
- **Deployment**: Render.com
- **Security**: Session-based authentication, environment variables

## 📋 Quick Start

### Prerequisites
- Python 3.8+
- Git

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/family-tree-explorer.git
   cd family-tree-explorer
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

5. **Run the application:**
   ```bash
   python3 app.py
   ```

6. **Open your browser:**
   ```
   http://localhost:5001
   ```

## 🔐 Admin Access

The admin panel is password-protected. Default development password is set in `.env` file.

- **Admin Login**: `/admin/login`
- **Features**: View submissions, export data, manage feedback

## 📊 Statistics

- **727 Individuals** in the family database
- **204 Family units** documented
- **Multi-generational** spanning several centuries
- **International connections** across Ghana, Germany, US, Canada, and UK

## 🎯 Key People Featured

- **Dr. Ebenezer Ako Adjei** (1916-2002) - One of Ghana's "Big Six" independence leaders
- **Extensive Adjei family lineage** with detailed historical documentation
- **International family connections** across multiple continents

## 🔧 Configuration

### Environment Variables

```bash
# Required
ADMIN_PASSWORD=your_secure_admin_password
SECRET_KEY=your_random_secret_key

# Optional
PORT=5001
FLASK_ENV=development
GEDCOM_FILE=your-family-file.ged
```

### GEDCOM File Format

The application supports GEDCOM 5.5.1 format files. Place your `.ged` file in the project root and update the `GEDCOM_FILE` environment variable.

## 🚀 Deployment

### Deploy to Render (Recommended)

1. **Fork this repository**
2. **Connect to Render:**
   - Go to [render.com](https://render.com)
   - Connect your GitHub account
   - Select this repository
3. **Set environment variables:**
   - `ADMIN_PASSWORD`: Your secure admin password
   - `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
   - `FLASK_ENV`: `production`
4. **Deploy!**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### Other Platforms

See `DEPLOYMENT.md` for detailed instructions for:
- Heroku
- DigitalOcean App Platform
- Traditional servers

## 📚 API Endpoints

- `GET /` - Homepage
- `GET /explore` - Main family tree interface
- `GET /search?q=name` - Search for family members
- `GET /person/{id}` - Get person details
- `GET /stats` - Family statistics
- `POST /submit_update` - Submit family corrections
- `POST /submit_feedback` - Submit feedback

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🛡️ Security

- Environment variables for sensitive data
- Session-based authentication
- Input validation and sanitization
- HTTPS in production (recommended)

## 📞 Support

- 📧 **Email**: [your-email@example.com]
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/family-tree-explorer/issues)
- 📖 **Documentation**: See `DEPLOYMENT.md` for detailed setup

## 🎉 Acknowledgments

- Built with ❤️ for family history preservation
- Genealogy data managed with care and respect for privacy
- Special thanks to family members who contributed historical information

---

**🌳 Preserving family history, one connection at a time.** 