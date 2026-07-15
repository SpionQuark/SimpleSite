/* Usage:
*
*   <auto-form>{{ schema | tojson }}<auto-form>
*
*/ 
customElements.define(
    "auto-form",
    class AutoForm extends HTMLElement {
        mapType(type) {
            const map = {
                text: "text",
                number: "number",
                checkbox: "checkbox",
            };
            return map[type] || "text";
        }

        connectedCallback() {
            console.log(this.textContent.trim());
            const schema = JSON.parse(this.textContent.trim());
            this.textContent = "";

            const form = document.createElement("form");
            form.method = "POST";
            form.action = schema.endpoint;

            for (const field of schema.fields) {
                const input = document.createElement("input");
                input.name = field.name;
                input.type = this.mapType(field.type);

                if (field.type === "checkbox") {
                    input.checked = !!field.default;
                } else if (field.default !== null) {
                    input.value = field.default;
                }

                if (field.required) input.required = true;

                form.appendChild(input);
            }
            const field = document.createElement("input");
            field.name = "data";
            field.value = JSON.stringify(schema);
            // field.style.display = "hidden";
            form.append(field)

            const submit = document.createElement("button");
            submit.textContent = "Submit";
            form.appendChild(submit);

            this.appendChild(form);
        }
    },
);