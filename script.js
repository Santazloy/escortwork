// Enhanced mouse and touch tracking for cards with neon glow
document.querySelectorAll('.card').forEach(card => {
  // Mouse events
  card.addEventListener('mouseenter', () => {
    card.style.setProperty('--mouse-x', '50%');
    card.style.setProperty('--mouse-y', '50%');
  });

  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    card.style.setProperty('--mouse-x', x + '%');
    card.style.setProperty('--mouse-y', y + '%');
  });

  card.addEventListener('mouseleave', () => {
    card.style.setProperty('--mouse-x', '50%');
    card.style.setProperty('--mouse-y', '50%');
  });

  // Touch events with improved handling
  card.addEventListener('touchstart', e => {
    const touch = e.touches[0];
    const rect = card.getBoundingClientRect();
    const x = ((touch.clientX - rect.left) / rect.width) * 100;
    const y = ((touch.clientY - rect.top) / rect.height) * 100;
    card.style.setProperty('--mouse-x', x + '%');
    card.style.setProperty('--mouse-y', y + '%');
    card.classList.add('touch-active');
  }, { passive: true });

  card.addEventListener('touchmove', e => {
    const touch = e.touches[0];
    const rect = card.getBoundingClientRect();
    const x = Math.max(0, Math.min(100, ((touch.clientX - rect.left) / rect.width) * 100));
    const y = Math.max(0, Math.min(100, ((touch.clientY - rect.top) / rect.height) * 100));
    card.style.setProperty('--mouse-x', x + '%');
    card.style.setProperty('--mouse-y', y + '%');
  }, { passive: true });

  card.addEventListener('touchend', () => {
    // Delay removing the active class for a smoother transition
    setTimeout(() => {
      card.classList.remove('touch-active');
      card.style.setProperty('--mouse-x', '50%');
      card.style.setProperty('--mouse-y', '50%');
    }, 150);
  });

  card.addEventListener('touchcancel', () => {
    card.classList.remove('touch-active');
    card.style.setProperty('--mouse-x', '50%');
    card.style.setProperty('--mouse-y', '50%');
  });
});

// Smooth scroll behavior
document.documentElement.style.scrollBehavior = 'smooth';

// Form functions
function toggleExperienceDetails() {
  const value = document.getElementById('experience').value;
  const details = document.getElementById('experienceDetails');

  if (value === 'yes') {
    details.style.display = 'block';
    details.style.animation = 'fadeIn 0.4s ease';
  } else {
    details.style.display = 'none';
  }
}

async function submitForm() {
  const required = ['name', 'age', 'height', 'weight', 'citizenship', 'telegram', 'whatsapp'];
  for (const id of required) {
    const element = document.getElementById(id);
    if (!element.value.trim()) {
      element.focus();
      element.style.borderColor = 'rgba(255, 100, 100, 0.5)';
      element.style.boxShadow = '0 0 20px rgba(255, 100, 100, 0.2)';
      setTimeout(() => {
        element.style.borderColor = '';
        element.style.boxShadow = '';
      }, 2000);
      alert('Пожалуйста, заполните все обязательные поля');
      return;
    }
  }

  // Create FormData for file upload
  const formData = new FormData();

  // Add text fields
  formData.append('name', document.getElementById('name').value);
  formData.append('age', document.getElementById('age').value);
  formData.append('height', document.getElementById('height').value);
  formData.append('weight', document.getElementById('weight').value);
  formData.append('citizenship', document.getElementById('citizenship').value);
  formData.append('telegram', document.getElementById('telegram').value);
  formData.append('whatsapp', document.getElementById('whatsapp').value);
  formData.append('experience', document.getElementById('experience').value);
  formData.append('countries', document.getElementById('countries').value || '');

  // Add photos
  const photosInput = document.getElementById('photos');
  if (photosInput.files.length > 0) {
    Array.from(photosInput.files).forEach(photo => {
      formData.append('photos', photo);
    });
  }

  // Show loading state
  const submitBtn = document.querySelector('.submit-btn');
  const originalText = submitBtn.textContent;
  submitBtn.textContent = 'Отправка...';
  submitBtn.disabled = true;
  submitBtn.style.opacity = '0.7';

  try {
    const response = await fetch('/api/submit', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (result.success) {
      // Show success message
      const successMsg = document.getElementById('successMessage');
      successMsg.classList.add('show');

      // Clear form
      document.querySelectorAll('.form-input, .form-select, .form-textarea, .form-file').forEach(field => {
        field.value = '';
      });
      document.getElementById('experienceDetails').style.display = 'none';

      // Scroll to success message
      successMsg.scrollIntoView({ behavior: 'smooth', block: 'center' });

      setTimeout(() => successMsg.classList.remove('show'), 5000);
    } else {
      alert('Ошибка при отправке: ' + result.message);
    }
  } catch (error) {
    console.error('Ошибка:', error);
    alert('Ошибка соединения с сервером. Убедитесь, что сервер запущен.');
  } finally {
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
    submitBtn.style.opacity = '';
  }
}

// Navigation with smooth transitions
function showSection(id) {
  const mainPage = document.getElementById('mainPage');
  const section = document.getElementById(id);

  mainPage.style.opacity = '0';
  mainPage.style.transform = 'translateY(-20px)';

  setTimeout(() => {
    mainPage.style.display = 'none';
    section.classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, 300);
}

function goBack() {
  const mainPage = document.getElementById('mainPage');

  document.querySelectorAll('.section-page.active').forEach(section => {
    section.style.opacity = '0';
    section.style.transform = 'translateY(20px)';

    setTimeout(() => {
      section.classList.remove('active');
      section.style.opacity = '';
      section.style.transform = '';

      mainPage.style.display = 'flex';
      mainPage.style.opacity = '';
      mainPage.style.transform = '';

      window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 300);
  });
}

// Add transition styles
const style = document.createElement('style');
style.textContent = `
  #mainPage, .section-page {
    transition: opacity 0.3s ease, transform 0.3s ease;
  }
`;
document.head.appendChild(style);