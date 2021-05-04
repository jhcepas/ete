// Functions for upload_tree.html.

import { escape_html, hash, assert, storage_get, storage_remove,
         api_post, api_login, is_valid_token } from "./api.js";


document.addEventListener("DOMContentLoaded", on_load_page);


// Setup.
async function on_load_page() {
    // Make sure we start by being correctly logged in.
    const login = storage_get("login");
    if (!login || !(await is_valid_token(login.token)))
        await api_login("guest");

    if (!check_metadata.checked)  // if we reload the page, it may be checked
        div_metadata.style.display = "none";

    show_upload();
}


// Show the upload section and hide the login one.
function show_upload() {
    div_login.style.display = "none";
    div_upload.style.display = "block";

    const login = storage_get("login");
    div_info.innerHTML = `
        Logged in as <span title="${login.name}">${login.username}</span><br>
        <a href="#" onclick="show_login(); return false;">Log out</a>`;
}


// Show the login section and hide the upload one. Remove any login first.
function show_login() {
    storage_remove("login");

    div_upload.style.display = "none";
    div_login.style.display = "block";

    div_info.innerHTML = "";
}
window.show_login = show_login;


// Login-related functions.

// When the login button is pressed.
button_login.addEventListener("click", async () => {
    try {
        await api_login(input_username.value, input_password.value);
        show_upload();
    }
    catch (ex) {
        Swal.fire({html: ex.message, icon: "warning", timer: 5000,
                   toast: true, position: "top-end"});
    }
});

div_login.addEventListener("keyup", event => {
    if (event.key === "Enter")
        button_login.click();
});

button_guest.addEventListener("click", async () => {
    await api_login("guest");
    show_upload();
});


// Upload-related functions.

// When the upload button is pressed.
button_upload.addEventListener("click", async () => {
    try {
        await assert(input_name.value || !check_metadata.checked, "Missing name");

        const [name, description] = check_metadata.checked ?
            [input_name.value, input_description.value] :
            [hash(Date.now().toString()), ""];

        await assert(!input_trees_file.disabled || !input_newick_string.disabled,
                     "You need to supply a newick string or select a file");

        const data = new FormData();
        data.append("name", name);
        data.append("description", description);
        if (!input_newick_string.disabled)
            data.append("newick", input_newick_string.value.trim());
        else
            data.append("trees", await get_trees_file());

        const resp = await api_post("/trees", data);

        show_uploaded_trees(resp);
    }
    catch (ex) {
        Swal.fire({html: ex.message, icon: "warning",
                   toast: true, position: "top-end"});
    }
});


// Return the file containing the tree(s) as a newick or nexus.
async function get_trees_file() {
    await assert(input_trees_file.files.length > 0, "Missing file");

    const size_MB = input_trees_file.files[0].size / 1e6;
    await assert (size_MB < 30,
        `Sorry, the file is too big<br>` +
        `(${size_MB.toFixed(1)} MB, the maximum is 30 MB)`);

    return input_trees_file.files[0];
}


// Show the different added trees and allow to go explore them.
function show_uploaded_trees(resp) {
    const names = Object.keys(resp["ids"]);

    const link = name => `<a href="gui.html?` +
        `tree=${encodeURIComponent(name)}">${escape_html(name)}</a>`;

    if (names.length >= 1)
        Swal.fire({
            title: "Uploading Successful",
            html: "Added trees: " + names.map(link).join(", "),
            icon: "success",
            confirmButtonText: "Explore" + (names.length > 1 ? " the first" : ""),
            showCancelButton: true,
        }).then(result => {
            if (result.isConfirmed)
                window.location.href =
                    "gui.html?tree=" + encodeURIComponent(names[0]);
        });
    else
        Swal.fire({html: "Could not find any tree in file.", icon: "warning"});
}


// Load an example of a newick into the input text area.
function load_example() {
    radio_string.click();

    input_newick_string.value = `
((((((((((('Escherichia coli_D':0.001,'Escherichia coli':0.001)Escherichia:0.001,('Escherichia dysenteriae':0.002,'Escherichia flexneri':0.001)Escherichia:0.001)Escherichia:0.001,'Escherichia fergusonii':0.005)Escherichia:0.001,'Escherichia coli_C':0.001)Escherichia:0.001,'Escherichia sp002965065':0.004)Escherichia:0.001,(((('Escherichia sp004211955':0.001,'Escherichia sp005843885':0.001)Escherichia:0.001,'Escherichia sp001660175':0.002)Escherichia:0.001,'Escherichia marmotae':0.003)Escherichia:0.001,'Escherichia sp000208585':0.003)Escherichia:0.001)Escherichia:0.001,'Escherichia albertii':0.005)Escherichia:0.016,(((('Salmonella diarizonae':0.003,'Salmonella houtenae':0.003)Salmonella:0.001,'Salmonella arizonae':0.005)Salmonella:0.001,'Salmonella enterica':0.002)Salmonella:0.003,'Salmonella bongori':0.007)Salmonella:0.009)Enterobacteriaceae:0.004,(((('Citrobacter_A amalonaticus_C':0.006,'Citrobacter_A farmeri':0.003)Citrobacter_A:0.002,'Citrobacter_A amalonaticus':0.004)Citrobacter_A:0.006,('Citrobacter_A rodentium':0.011,'Citrobacter_A sedlakii':0.006)Citrobacter_A:0.006)Citrobacter_A:0.004,'Citrobacter_C amalonaticus_A':0.017)Enterobacteriaceae:0.002)Enterobacteriaceae:0.002,'Citrobacter_B koseri':0.014)Enterobacteriaceae:0.004,((((((('Citrobacter freundii_E':0.002,'Citrobacter europaeus':0.002)Citrobacter:0.001,'Citrobacter braakii':0.003)Citrobacter:0.001,'Citrobacter freundii_A':0.003)Citrobacter:0.001,'Citrobacter freundii':0.002)Citrobacter:0.001,(('Citrobacter portucalensis_A':0.002,'Citrobacter werkmanii':0.002)Citrobacter:0.003,'Citrobacter portucalensis':0.001)Citrobacter:0.001)Citrobacter:0.002,('Citrobacter youngae':0.001,'Citrobacter sp005281345':0.003)Citrobacter:0.002)Citrobacter:0.004,(('Citrobacter gillenii':0.005,'Citrobacter sp004684345':0.004)Citrobacter:0.007,'Citrobacter murliniae':0.007)Citrobacter:0.002)Citrobacter:0.011);
        `.trim();
}
window.load_example = load_example;


// Radio buttons and checkboxes.

radio_file.addEventListener("click", () => {
    input_trees_file.disabled = false;
    input_newick_string.disabled = true;
});

radio_string.addEventListener("click", () => {
    input_newick_string.disabled = false;
    input_trees_file.disabled = true;
});

check_metadata.addEventListener("change", () => {
    div_metadata.style.display = check_metadata.checked ? "block" : "none";
});
