// === UI Helper ===
function createProductCardHTML(product) {
  const link = product.link && product.link.startsWith("http") ? product.link : null;
  return `
    <div class="product-card">
      <img src="${product.thumbnail}" alt="${product.title}" width="100">
      <div>
        <p><strong>${product.title || "Untitled Product"}</strong></p>
        <p>${product.price || ""} - ${product.source || ""}</p>
        ${link ? `<a href="${link}" target="_blank">View Product</a>` : `<p><em>Link not available</em></p>`}
      </div>
    </div>
  `;
}

function sendImage() {
  const input = document.getElementById("imageInput");
  const file = input.files[0];
  const messagesDiv = document.getElementById("messages");
  const previewBox = document.getElementById("previewBox");
  const loader = document.getElementById("loader");
  const cheapLinkDiv = document.getElementById("cheapLink");
  const expensiveLinkDiv = document.getElementById("expensiveLink");

  // Clear previous results
  messagesDiv.innerHTML = '';
  previewBox.innerHTML = '';
  cheapLinkDiv.innerHTML = '';
  expensiveLinkDiv.innerHTML = '';
  loader.style.display = 'none';

  if (!file) return alert("Please upload an image.");

  // Show image preview
  const reader = new FileReader();
  reader.onload = e => {
    const img = document.createElement('img');
    img.src = e.target.result;
    img.style.maxWidth = '100%';
    img.style.maxHeight = '200px';
    img.style.borderRadius = '8px';
    previewBox.appendChild(img);
  };
  reader.readAsDataURL(file);

  const formData = new FormData();
  formData.append("image", file);

  messagesDiv.innerHTML += `<p><strong>You:</strong> [Image uploaded]</p>`;
  messagesDiv.innerHTML += `<p><em>Analyzing your style...</em></p>`;
  loader.style.display = 'block';

  // Cache-busting timestamp added to prevent stale responses
  fetch("/analyze?" + new Date().getTime(), {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      loader.style.display = 'none';
      messagesDiv.innerHTML += `<p><strong>Bot:</strong> ${data.description}</p>`;

      if (data.links && data.links.length > 0) {
        messagesDiv.innerHTML += `<p><strong>🛍️ Shop the Look:</strong></p>`;
        data.links.forEach(product => {
          messagesDiv.innerHTML += createProductCardHTML(product);
        });

        // Split into cheap/expensive options
        if (data.links[0]) cheapLinkDiv.innerHTML = createProductCardHTML(data.links[0]);
        if (data.links[1]) expensiveLinkDiv.innerHTML = createProductCardHTML(data.links[1]);
      } else {
        messagesDiv.innerHTML += `<p><em>No product links found.</em></p>`;
      }
    })
    .catch(err => {
      console.error("Error during image analysis:", err);
      loader.style.display = 'none';
      messagesDiv.innerHTML += `<p><strong>Bot:</strong> An error occurred while processing your image. Please try again.</p>`;
    });
}

function sendChat() {
  const input = document.getElementById("chatInput");
  const text = input.value.trim();
  const messages = document.getElementById("messages");

  if (!text) return;
  messages.innerHTML += `<p><strong>You:</strong> ${text}</p>`;
  input.value = "";

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text })
  })
    .then(res => res.json())
    .then(data => {
      messages.innerHTML += `<p><strong>Bot:</strong> ${data.reply}</p>`;
    })
    .catch(err => {
      console.error(err);
      messages.innerHTML += `<p><strong>Bot:</strong> Something went wrong.</p>`;
    });
}
