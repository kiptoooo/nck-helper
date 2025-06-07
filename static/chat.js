const toggle = document.getElementById("chat-toggle");
const chatBox = document.getElementById("chat-box");
const messages = document.getElementById("messages");

toggle.onclick = () => chatBox.style.display = chatBox.style.display === 'none' ? 'flex' : 'none';

async function sendMessage() {
  const input = document.getElementById("user-input");
  const msg = input.value;
  if (!msg) return;
  messages.innerHTML += `<div><strong>You:</strong> ${msg}</div>`;
  input.value = "";
  const res = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  });
  const data = await res.json();
  messages.innerHTML += `<div><strong>Bot:</strong> ${data.reply}</div>`;
  messages.scrollTop = messages.scrollHeight;
}