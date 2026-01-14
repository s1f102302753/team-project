// --- CSRF TOKEN 取得 ---
function getCSRFToken() {
    let token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : "";
}

// --- PDF Upload ---
document.getElementById("upload-form").addEventListener("submit", function(event){
    event.preventDefault();

    let fileField = document.getElementById("pdf-file").files[0];
    if (!fileField) {
        alert("PDFを選択してください。");
        return;
    }

    let formData = new FormData();
    formData.append("pdf", fileField);

    fetch("/chatbot/upload/", {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        alert("PDF のインデックス作成が完了しました！");
        console.log(data);
    })
    .catch(error => console.error("Upload Error:", error));
});

// --- Chat Ask ---
document.getElementById("chat-form").addEventListener("submit", function(event){
    event.preventDefault();

    let question = document.getElementById("question").value;
    if (!question) return;

    fetch("/chatbot/ask/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ question: question })
    })
    .then(response => response.json())
    .then(data => {
        let box = document.getElementById("chatbox");
        box.innerHTML += "You: " + question + "\n";

        let reply = data.answer ? data.answer : "Error: " + data.error;
        box.innerHTML += "Bot: " + reply + "\n\n";
    })
    .catch(error => console.error("Ask Error:", error));
});
