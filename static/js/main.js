(function() {
    'use strict';

    const particlesContainer = document.getElementById('particles');
    const themeToggle = document.getElementById('themeToggle');
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');
    const backToTop = document.getElementById('backToTop');
    const contactForm = document.getElementById('contactForm');
    const yearSpan = document.getElementById('year');

    function createParticles() {
        const particleCount = window.innerWidth < 768 ? 30 : 60;
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            particle.style.left = Math.random() * 100 + '%';
            particle.style.width = Math.random() * 4 + 2 + 'px';
            particle.style.height = particle.style.width;
            particle.style.animationDuration = Math.random() * 15 + 10 + 's';
            particle.style.animationDelay = Math.random() * 10 + 's';
            particlesContainer.appendChild(particle);
        }
    }

    function initTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        } else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
            document.documentElement.setAttribute('data-theme', 'light');
        }
    }

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    });

    navToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        navToggle.classList.toggle('active');
    });

    document.querySelectorAll('.nav-links a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            navToggle.classList.remove('active');
        });
    });

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');

                const slideLeft = entry.target.querySelector('.slide-in-left');
                const slideRight = entry.target.querySelector('.slide-in-right');
                const slideItems = entry.target.querySelectorAll('.slide-in-item');

                if (slideLeft) {
                    setTimeout(() => slideLeft.classList.add('animated'), 100);
                }
                if (slideRight) {
                    setTimeout(() => slideRight.classList.add('animated'), 250);
                }
                slideItems.forEach(item => item.classList.add('animated'));

                const progressBars = entry.target.querySelectorAll('.skill-progress');
                progressBars.forEach(bar => {
                    const level = bar.getAttribute('data-level');
                    bar.style.setProperty('--level', level + '%');
                    bar.classList.add('animated');
                });
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));

    document.querySelectorAll('.skill-category').forEach(card => {
        card.addEventListener('mouseenter', () => {
            setTimeout(() => {
                const progressBars = card.querySelectorAll('.skill-progress');
                progressBars.forEach(bar => {
                    const level = bar.getAttribute('data-level');
                    bar.style.setProperty('--level', level + '%');
                    bar.classList.add('animated');
                });
            }, 250);
        });
        card.addEventListener('mouseleave', () => {
            const progressBars = card.querySelectorAll('.skill-progress');
            progressBars.forEach(bar => {
                bar.classList.remove('animated');
                bar.style.setProperty('--level', '0%');
            });
        });
    });

    window.addEventListener('scroll', () => {
        if (window.scrollY > 500) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });

    backToTop.addEventListener('click', (e) => {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function showError(inputId, messageId, message) {
        const input = document.getElementById(inputId);
        const error = document.getElementById(messageId);
        input.classList.add('error');
        error.textContent = message;
    }

    function clearError(inputId, messageId) {
        const input = document.getElementById(inputId);
        const error = document.getElementById(messageId);
        input.classList.remove('error');
        error.textContent = '';
    }

    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        let isValid = true;

        clearError('name', 'nameError');
        clearError('email', 'emailError');
        clearError('message', 'messageError');

        const name = document.getElementById('name').value.trim();
        const email = document.getElementById('email').value.trim();
        const message = document.getElementById('message').value.trim();

        if (!name) {
            showError('name', 'nameError', 'Name is required');
            isValid = false;
        }
        if (!email) {
            showError('email', 'emailError', 'Email is required');
            isValid = false;
        } else if (!validateEmail(email)) {
            showError('email', 'emailError', 'Please enter a valid email');
            isValid = false;
        }
        if (!message) {
            showError('message', 'messageError', 'Message is required');
            isValid = false;
        }

        if (!isValid) return;

        const btn = contactForm.querySelector('.btn-submit');
        const btnText = btn.querySelector('.btn-text');
        const btnLoader = btn.querySelector('.btn-loader');
        const formStatus = document.getElementById('formStatus');

        btn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-flex';
        formStatus.textContent = '';

        try {
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, message })
            });

            const data = await response.json();

            if (response.ok) {
                formStatus.className = 'form-status success';
                formStatus.textContent = data.message;
                contactForm.reset();
            } else {
                formStatus.className = 'form-status error';
                formStatus.textContent = data.error || 'Something went wrong';
            }
        } catch (err) {
            formStatus.className = 'form-status error';
            formStatus.textContent = 'Failed to send message. Please try again.';
        } finally {
            btn.disabled = false;
            btnText.style.display = 'inline';
            btnLoader.style.display = 'none';
        }
    });

    yearSpan.textContent = new Date().getFullYear();

    function initHeroAnimations() {
        const nameEl = document.querySelector('.hero-name-text');
        const titleEl = document.querySelector('.hero-title-text');
        const cursorEl = document.querySelector('.cursor-blink');

        if (nameEl) {
            const text = nameEl.getAttribute('data-text');
            nameEl.innerHTML = '';
            [...text].forEach((char, i) => {
                const span = document.createElement('span');
                span.classList.add('char');
                span.textContent = char === ' ' ? '\u00A0' : char;
                span.style.animationDelay = `${0.6 + i * 0.06}s`;
                nameEl.appendChild(span);
            });
        }

        if (titleEl) {
            const titles = ['Junior Software Developer'];
            let titleIndex = 0;
            let charIndex = 0;
            let isDeleting = false;
            let isPaused = false;

            function type() {
                const currentTitle = titles[titleIndex];

                if (isPaused) {
                    setTimeout(() => {
                        isPaused = false;
                        isDeleting = true;
                        type();
                    }, 2000);
                    return;
                }

                if (!isDeleting) {
                    titleEl.innerHTML = currentTitle.substring(0, charIndex + 1);
                    charIndex++;
                    if (charIndex === currentTitle.length) {
                        isPaused = true;
                    }
                    setTimeout(type, 80);
                } else {
                    titleEl.innerHTML = currentTitle.substring(0, charIndex - 1);
                    charIndex--;
                    if (charIndex === 0) {
                        isDeleting = false;
                        titleIndex = (titleIndex + 1) % titles.length;
                    }
                    setTimeout(type, 40);
                }
            }

            setTimeout(() => {
                titleEl.style.opacity = '1';
                type();
            }, 1400);
        }
    }

    initTheme();
    createParticles();
    initHeroAnimations();
})();
