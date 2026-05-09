function addRow() {
    let container = document.getElementById("rows");
    let firstRow = container.firstElementChild;
    let clone = firstRow.cloneNode(true);

    // clear inputs
    clone.querySelectorAll("input").forEach(i => i.value = "");

    container.appendChild(clone);
}

document.addEventListener("wheel", function (event) {
    if (document.activeElement.type === "number") {
        document.activeElement.blur();
    }
});

function filterSalesman(selectElement) {
    let row = selectElement.parentElement;
    let dropdown = row.querySelector(".salesman");

    let type = selectElement.value;
    let currentBranch = "{{branch_id}}";

    let options = dropdown.querySelectorAll("option");

    options.forEach(option => {
        let branch = option.getAttribute("data-branch");

        if (type === "branch") {
            option.style.display = (branch == currentBranch) ? "block" : "none";
        } else {
            option.style.display = (branch != currentBranch) ? "block" : "none";
        }
    });

    dropdown.selectedIndex = 0;
}

function addSalaryRow() {
    let container = document.getElementById("salary_rows");
    let first = container.firstElementChild;
    let clone = first.cloneNode(true);

    clone.querySelector("input").value = "";

    container.appendChild(clone);
}

function addSalesCommRow() {
    let div = document.createElement("div");
    div.className = "salary_row";

    div.innerHTML = `
        <select name="sales_comm_salesman_id">
            ${document.querySelector('[name="salary_salesman_id"]').innerHTML}
        </select>
        <input name="sales_comm_amount" placeholder="Sales Commission">
    `;

    document.getElementById("sales_comm_rows").appendChild(div);
}

function addAdvanceRow() {

    let div = document.createElement("div");

    div.className = "salary_row";

    div.innerHTML = `

        <select name="advance_salesman_id">

            ${document.querySelector('[name="salary_salesman_id"]').innerHTML}

        </select>

        <select name="advance_type">

            <option value="debit">
                Debit (Money Given)
            </option>

            <option value="credit">
                Credit (Money Returned)
            </option>

        </select>

        <input
            name="advance_amount"
            type="number"
            placeholder="Amount"
        >

    `;

    document
        .getElementById("advance_rows")
        .appendChild(div);
}

document.addEventListener("keydown", function(e) {

    if (e.key === "Enter") {

        let tag = document.activeElement.tagName.toLowerCase();

        if (
            tag === "input" ||
            tag === "select"
        ) {

            e.preventDefault();

            let form = document.querySelector("form");

            let elements = Array.from(
                form.querySelectorAll(
                    "input, select, button"
                )
            ).filter(el => !el.disabled);

            let index = elements.indexOf(document.activeElement);

            if (index > -1 && index < elements.length - 1) {
                elements[index + 1].focus();
            }
        }
    }
});
