const chatPanel = document.getElementById('chat-panel');
const promptInput = document.getElementById('prompt-input');
const askButton = document.getElementById('ask-button');
const statusText = document.getElementById('status-text');

const addMessage = (text, type) => {
  const wrapper = document.createElement('div');
  wrapper.className = `message ${type}`;

  const label = document.createElement('div');
  label.className = 'message__label';
  label.textContent = type === 'user' ? 'You' : 'Analyst';

  const content = document.createElement('div');
  content.className = 'message__content';
  content.textContent = text;

  wrapper.appendChild(label);
  wrapper.appendChild(content);
  chatPanel.appendChild(wrapper);
  chatPanel.scrollTop = chatPanel.scrollHeight;
  return wrapper;
};

const showStatus = (text) => {
  statusText.textContent = text;
};

const drawChart = (item) => {
  const frame = document.createElement('div');
  frame.className = 'chart-frame';
  const canvas = document.createElement('canvas');
  frame.appendChild(canvas);
  chatPanel.appendChild(frame);
  chatPanel.scrollTop = chatPanel.scrollHeight;

  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: item.rows.map((row) => row.label),
      datasets: [
        {
          label: 'Total (₹)',
          data: item.rows.map((row) => row.total),
          backgroundColor: '#2563eb',
          borderRadius: 12,
        },
      ],
    },
    options: {
      plugins: {
        title: {
          display: true,
          text: `Sales by ${item.group_by}`,
          padding: { top: 8, bottom: 12 },
          font: { size: 16, weight: '600' },
        },
        legend: { display: false },
      },
      responsive: true,
      scales: {
        x: { grid: { display: false } },
        y: { ticks: { callback: (value) => `₹${value}` } },
      },
    },
  });
};

const ask = async () => {
  const message = promptInput.value.trim();
  if (!message) return;

  addMessage(message, 'user');
  promptInput.value = '';
  askButton.disabled = true;
  showStatus('Processing your request...');

  try {
    const response = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      const body = await response.text();
      throw new Error(`${response.status}: ${body}`);
    }

    const data = await response.json();
    addMessage(data.answer || 'No answer returned.', 'agent');

    if (Array.isArray(data.data)) {
      data.data.forEach((step) => {
        const result = step.result;
        if (result?.type === 'sales_report' && Array.isArray(result.rows) && result.rows.length) {
          drawChart(result);
        }
      });
    }

    showStatus('Completed successfully');
  } catch (error) {
    addMessage(`Error: ${error.message}`, 'agent');
    showStatus('Request failed');
  } finally {
    askButton.disabled = false;
    promptInput.focus();
  }
};

askButton.addEventListener('click', ask);
promptInput.addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    ask();
  }
});
