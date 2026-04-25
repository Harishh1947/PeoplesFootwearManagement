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