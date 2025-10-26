// Mouse and touch tracking for cards
document.querySelectorAll('.card').forEach(card => {
  // Mouse events
  card.addEventListener('mousemove', e => {
    const rect = card.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    card.style.setProperty('--mouse-x', x + '%');
    card.style.setProperty('--mouse-y', y + '%');
  });

  // Touch events
  card.addEventListener('touchstart', e => {
    const touch = e.touches[0];
    const rect = card.getBoundingClientRect();
    const x = ((touch.clientX - rect.left) / rect.width) * 100;
    const y = ((touch.clientY - rect.top) / rect.height) * 100;
    card.style.setProperty('--mouse-x', x + '%');
    card.style.setProperty('--mouse-y', y + '%');
    card.classList.add('touch-active');
  });

  card.addEventListener('touchmove', e => {
    const touch = e.touches[0];
    const rect = card.getBoundingClientRect();
    const x = ((touch.clientX - rect.left) / rect.width) * 100;
    const y = ((touch.clientY - rect.top) / rect.height) * 100;
    card.style.setProperty('--mouse-x', x + '%');
    card.style.setProperty('--mouse-y', y + '%');
  });

  card.addEventListener('touchend', () => {
    card.classList.remove('touch-active');
  });
});

// Form functions
function toggleExperienceDetails() {
  const value = document.getElementById('experience').value;
  const details = document.getElementById('experienceDetails');
  details.style.display = value === 'yes' ? 'block' : 'none';
}

async function submitForm() {
  const required = ['name', 'age', 'height', 'weight', 'citizenship', 'telegram', 'whatsapp'];
  for (const id of required) {
    if (!document.getElementById(id).value.trim()) {
      alert('Пожалуйста, заполните все обязательные поля');
      return;
    }
  }

  // Создаем FormData для отправки файлов
  const formData = new FormData();

  // Добавляем текстовые поля
  formData.append('name', document.getElementById('name').value);
  formData.append('age', document.getElementById('age').value);
  formData.append('height', document.getElementById('height').value);
  formData.append('weight', document.getElementById('weight').value);
  formData.append('citizenship', document.getElementById('citizenship').value);
  formData.append('telegram', document.getElementById('telegram').value);
  formData.append('whatsapp', document.getElementById('whatsapp').value);
  formData.append('experience', document.getElementById('experience').value);
  formData.append('countries', document.getElementById('countries').value || '');

  // Добавляем фото
  const photosInput = document.getElementById('photos');
  if (photosInput.files.length > 0) {
    Array.from(photosInput.files).forEach(photo => {
      formData.append('photos', photo);
    });
  }

  // Показываем индикатор загрузки
  const submitBtn = document.querySelector('.submit-btn');
  const originalText = submitBtn.textContent;
  submitBtn.textContent = 'Отправка...';
  submitBtn.disabled = true;

  try {
    // Отправляем на сервер
    const response = await fetch('/api/submit', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (result.success) {
      // Показываем сообщение об успехе
      const successMsg = document.getElementById('successMessage');
      successMsg.classList.add('show');

      // Очищаем форму
      document.querySelectorAll('.form-input, .form-select, .form-textarea, .form-file').forEach(field => {
        field.value = '';
      });
      document.getElementById('experienceDetails').style.display = 'none';

      setTimeout(() => successMsg.classList.remove('show'), 5000);
    } else {
      alert('Ошибка при отправке: ' + result.message);
    }
  } catch (error) {
    console.error('Ошибка:', error);
    alert('Ошибка соединения с сервером. Убедитесь, что сервер запущен.');
  } finally {
    // Возвращаем кнопку в исходное состояние
    submitBtn.textContent = originalText;
    submitBtn.disabled = false;
  }
}

// Navigation
function showSection(id) {
  document.getElementById('mainPage').style.display = 'none';
  document.getElementById(id).classList.add('active');
}

function goBack() {
  document.querySelectorAll('.section-page').forEach(section => {
    section.classList.remove('active');
  });
  document.getElementById('mainPage').style.display = 'flex';
}