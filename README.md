# Review Loop ☕⭐

Review Loop is a smart customer feedback and review management platform built for cafes and restaurants.

It helps businesses:

- Collect instant customer feedback
- Redirect happy customers to Google Reviews
- Capture unhappy customer pain points privately
- Improve customer experience using structured insights

---

## 🚀 Live Demo

https://your-render-url.onrender.com/

---

## ✨ Features

### Customer Experience Flow

✅ Cafe listing homepage  
✅ Cafe branding (logo + name)  
✅ Mobile-friendly review UI  
✅ 1–5 star rating system  

### Smart Feedback Logic

**Positive reviews (4–5 stars):**
- Thank-you screen
- Redirect to Google Review page

**Negative reviews (1–3 stars):**
- Private structured feedback collection
- Issue categories:
  - Food
  - Service
  - Delay
  - Cleanliness
- Optional customer comments

---

## 🧠 Business Value

This platform helps businesses:

- Increase public positive reviews
- Capture negative feedback before it becomes public
- Understand customer pain points
- Improve operations using real feedback

---

## 🛠 Tech Stack

### Backend
- Python
- Django

### Database
- PostgreSQL

### Media Storage
- Cloudinary

### Static Files
- WhiteNoise

### Deployment
- Render

---

## 📁 Project Structure

```bash
review_loop/
│
├── feedback_loop/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│
├── reviews/
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   ├── urls.py
│   ├── templates/
│   │   └── reviews/
│   │       ├── home.html
│   │       ├── cafe.html
│   │       └── thank_you.html
│
├── requirements.txt
├── Procfile
└── README.md
```

---

## ⚙️ Installation (Local Setup)

Clone repo:

```bash
git clone https://github.com/yourusername/review-loop.git
cd review-loop
```

Create virtual environment:

```bash
python -m venv venv
```

Activate:

Windows:

```bash
venv\Scripts\activate
```

Mac/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create `.env`

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=your-db-url
CLOUDINARY_URL=your-cloudinary-url
```

---

## Database Setup

Run:

```bash
python manage.py migrate
```

Create admin:

```bash
python manage.py createsuperuser
```

Run server:

```bash
python manage.py runserver
```

---

## 🌐 Production Deployment

Configured for deployment with:

- Render
- Gunicorn
- PostgreSQL
- Cloudinary
- WhiteNoise

---

## Admin Panel

Access:

```bash
/admin/
```

Manage:

- Cafes
- Feedback entries
- Logos
- Review links

---

## Future Improvements

Planned features:

- QR code generation per cafe
- WhatsApp complaint alerts
- Daily feedback summary emails
- AI-generated review insights
- Dashboard analytics
- Multi-tenant cafe onboarding
- Subscription billing

---

## Problem Being Solved

Most happy customers never leave reviews.

Most unhappy customers leave silently—or publicly complain.

Review Loop creates a frictionless system to:

- Encourage positive public reviews
- Collect private actionable feedback
- Help businesses improve faster

---

## License

MIT License

---

## Author

Built by Nishant Dave 🚀
