# emicyber Portfolio

A modern, responsive portfolio website built with Flask.

## Features

- Dark/Light mode toggle with system preference detection
- Animated particle background
- Smooth scroll animations on viewport entry
- Responsive mobile-first design
- Contact form with validation
- Resume/CV download

## Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python app.py
   ```

4. Visit http://localhost:5000

## Customize

- Update personal info in `templates/index.html`
- Replace placeholder avatar with your photo
- Add your resume to `static/assets/resume.pdf`
- Update project links and descriptions
- Modify skill levels via `data-level` attributes
