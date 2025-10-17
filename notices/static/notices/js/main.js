document.addEventListener("DOMContentLoaded", function() {
    const buttons = document.querySelectorAll("#taskbar button");
    const contents = document.querySelectorAll(".tab-content");

    buttons.forEach(button => {
        button.addEventListener("click", () => {
            const target = button.dataset.target;
            contents.forEach(c => c.style.display = "none");  // すべて非表示
            document.getElementById(target).style.display = "block";  // 押したタブを表示
        });
    });
});
