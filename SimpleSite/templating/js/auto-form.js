/* Usage:
*
*   <auto-form>{{ schema | tojson }}<auto-form>
*
*/ 

customElements.define(
    "auto-form",
    class AutoForm extends HTMLElement {
        connectedCallback() {
            const schema = JSON.parse(this.textContent.trim());
            this.textContent = "";
            
            const form = document.createElement("form");
            form.method = schema.method;
            form.action = schema.endpoint;

            for (const field of schema.fields){
                const input = document.createElement("input");
                input.name = field.name;
                input.type = mapType(field.type); // str / int / bool → input type mapping
                if (field.default !== null) input.value = field.default;
                if (field.required) input.required = true;
            }

            const submit = document.createElement("button");
            submit.textContent = "Submit";
            form.appendChild(submit);

            this.appendChild(form);
        }
});
