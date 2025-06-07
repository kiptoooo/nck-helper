const toggle = document.getElementById("chat-toggle"),
      box    = document.getElementById("chat-box"),
      msgs   = document.getElementById("messages");

toggle.onclick = ()=> {
  box.style.display = box.style.display === "flex" ? "none" : "flex";
};

function sendMessage(){
  let inp = document.getElementById("user-input"),
      text = inp.value.trim();
  if(!text) return;
  msgs.innerHTML += `<div><strong>You:</strong> ${text}</div>`;
  inp.value="";
  fetch("/chat", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({message:text})
  })
  .then(r=>r.json())
  .then(d=>{
    msgs.innerHTML += `<div><strong>Assistant:</strong> ${d.reply}</div>`;
    msgs.scrollTop = msgs.scrollHeight;
  });
}
