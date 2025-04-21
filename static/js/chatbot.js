// document.addEventListener('DOMContentLoaded', function () {
//     const sendBtn = document.getElementById('send-btn');
//     const chatInput = document.getElementById('chat-input');
//     const chatMessages = document.getElementById('chat-messages');
//     const previewContainer = document.getElementById('post-preview-container');

//     const linkedinBody = document.getElementById('linkedin-body');
//     const twitterBody = document.getElementById('twitter-body');
//     const redditBody = document.getElementById('reddit-body');

//     sendBtn.addEventListener('click', async function () {
//         const userPrompt = chatInput.value.trim();
//         if (!userPrompt) return;

//         const userMessage = document.createElement('div');
//         userMessage.className = 'user-message';
//         userMessage.innerText = userPrompt;
//         chatMessages.appendChild(userMessage);

//         sendBtn.disabled = true;
//         sendBtn.innerText = "Generating...";

//         const platforms = Array.from(document.querySelectorAll('input[name="platforms"]:checked')).map(el => el.value);

//         try {
//             const response = await fetch('/api/generate', {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 credentials: 'include', // IMPORTANT: ensures cookie is sent
//                 body: JSON.stringify({ content: userPrompt, platforms })
//             });

//             const data = await response.json();

//             if (data.linkedin) linkedinBody.innerText = data.linkedin;
//             if (data.twitter) twitterBody.innerText = data.twitter;
//             if (data.reddit) redditBody.innerText = data.reddit;

//             previewContainer.style.display = 'block';

//         } catch (error) {
//             console.error("Error:", error);
//             alert("Something went wrong while generating posts.");
//         } finally {
//             sendBtn.disabled = false;
//             sendBtn.innerText = "Generate";
//             chatInput.value = '';
//         }
//     });

//     document.querySelectorAll('.post-tab').forEach(tab => {
//         tab.addEventListener('click', () => {
//             const platform = tab.dataset.platform;
//             document.querySelectorAll('.post-tab').forEach(t => t.classList.remove('active'));
//             document.querySelectorAll('.post-content').forEach(c => c.classList.remove('active'));
//             tab.classList.add('active');
//             document.getElementById(`${platform}-content`).classList.add('active');
//         });
//     });

//     document.querySelectorAll('.copy-btn').forEach(button => {
//         button.addEventListener('click', () => {
//             const platform = button.dataset.platform;
//             const content = document.getElementById(`${platform}-body`).innerText;
//             navigator.clipboard.writeText(content).then(() => {
//                 button.innerText = 'Copied!';
//                 setTimeout(() => button.innerText = 'Copy', 2000);
//             });
//         });
//     });
// });


document.addEventListener('DOMContentLoaded', function () {
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const previewContainer = document.getElementById('post-preview-container');

    const linkedinBody = document.getElementById('linkedin-body');
    const twitterBody = document.getElementById('twitter-body');
    const redditBody = document.getElementById('reddit-body');

    sendBtn.addEventListener('click', async function () {
        const userPrompt = chatInput.value.trim();
        if (!userPrompt) return;

        const userMessage = document.createElement('div');
        userMessage.className = 'user-message message';
        userMessage.innerText = userPrompt;
        chatMessages.appendChild(userMessage);

        sendBtn.disabled = true;
        sendBtn.innerText = "Generating...";

        const platforms = Array.from(document.querySelectorAll('input[name="platforms"]:checked')).map(el => el.value);

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ content: userPrompt, platforms })
            });

            const data = await response.json();

            if (data.linkedin) linkedinBody.innerText = data.linkedin;
            if (data.twitter) twitterBody.innerText = data.twitter;
            if (data.reddit) redditBody.innerText = data.reddit;

            previewContainer.style.display = 'flex';

        } catch (error) {
            console.error("Error:", error);
            alert("Something went wrong while generating posts.");
        } finally {
            sendBtn.disabled = false;
            sendBtn.innerText = "Generate";
            chatInput.value = '';
        }
    });

    // Tab switching
    document.querySelectorAll('.post-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const platform = tab.dataset.platform;

            document.querySelectorAll('.post-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.post-content').forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(`${platform}-content`).classList.add('active');
        });
    });

    // Copy to clipboard
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', () => {
            const platform = button.dataset.platform;
            const content = document.getElementById(`${platform}-body`).innerText;

            navigator.clipboard.writeText(content).then(() => {
                button.innerText = 'Copied!';
                setTimeout(() => button.innerText = 'Copy', 2000);
            });
        });
    });

    // Close preview and clear posts
    document.querySelector('.close-preview-btn').addEventListener('click', () => {
        previewContainer.style.display = 'none';
        linkedinBody.innerText = '';
        twitterBody.innerText = '';
        redditBody.innerText = '';
    });
});
