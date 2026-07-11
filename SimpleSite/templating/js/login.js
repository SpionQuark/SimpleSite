customElements.define(
    "login-form",
    class LoginForm extends HTMLElement {
        constructor() {
            super();
            this.innerHTML = `
            <form method="post">
            <input name="user" placeholder="Username">
            <input name="password" type="password" placeholder="Password">
            <button type="submit">Log in</button>'
            </form>`;
        }
});
