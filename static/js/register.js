function togglePassword() {
    const password = document.getElementById("password");
    const confirm = document.getElementById("confirm_password");

    [password, confirm].forEach(field => {
        if (field) {
            field.type = field.type === "password" ? "text" : "password";
        }
    });
}