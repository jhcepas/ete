// Search-related functions.

import { view, menus, get_tid } from "./gui.js";
import { draw_tree } from "./draw.js";
import { api } from "./api.js";

export { search, remove_searches, get_search_class, colorize_searches };


// Search nodes in the server and redraw the tree (with the results too).
async function search() {
    let search_text;

    const result = await Swal.fire({
        input: "text",
        position: "bottom-start",
        inputPlaceholder: "Enter name or /r <regex> or /e <exp>",
        showConfirmButton: false,
        preConfirm: async text => {
            if (!text)
                return false;  // prevent popup from closing

            search_text = text;  // to be used when checking the result later on

            try {
                if (text in view.searches)
                    throw new Error("Search already exists.");

                const qs = `text=${encodeURIComponent(text)}`;
                return await api(`/trees/${get_tid()}/search?${qs}`);
            }
            catch (exception) {
                Swal.fire({
                    position: "bottom-start",
                    showConfirmButton: false,
                    html: exception,
                    icon: "error",
                });
            }
        },
    });

    if (result.isConfirmed) {
        const res = result.value;  // shortcut

        if (res.message === 'ok') {
            const colors = ["#FF0", "#F0F", "#0FF", "#F00", "#0F0", "#00F"];
            const nsearches = Object.keys(view.searches).length;

            view.searches[search_text] = {
                results: {n: res.nresults,
                          opacity: 0.4,
                          color: colors[nsearches % colors.length]},
                parents: {n: res.nparents,
                          color: "#000",
                          width: 5},
            };

            add_search_to_menu(search_text);

            draw_tree();
        }
        else {
            Swal.fire({
                position: "bottom-start",
                showConfirmButton: false,
                text: res.message,
                icon: "error",
            });
        }
    }
}


// Return a class name related to the results of searching for text.
function get_search_class(text, type="results") {
    return "search_" + type + "_" + text.replace(/[^A-Za-z0-9_-]/g, '');
}


// Add a folder to the menu that corresponds to the given search text
// and lets you change the result nodes color and so on.
function add_search_to_menu(text) {
    const folder = menus.tags_searches.__folders.searches.addFolder(text);

    const search = view.searches[text];

    search.remove = function() {
        delete view.searches[text];
        menus.tags_searches.__folders.searches.removeFolder(folder);
        draw_tree();
    }

    const folder_results = folder.addFolder(`results (${search.results.n})`);
    folder_results.add(search.results, "opacity", 0, 1).step(0.01).onChange(
        () => colorize_search(text));
    folder_results.addColor(search.results, "color").onChange(
        () => colorize_search(text));

    const folder_parents = folder.addFolder(`parents (${search.parents.n})`);
    folder_parents.addColor(search.parents, "color").onChange(
        () => colorize_search(text));
    folder_parents.add(search.parents, "width", 0.1, 20).onChange(
        () => colorize_search(text));

    folder.add(search, "remove");
}


function colorize_search(text) {
    const search = view.searches[text];

    const cresults = get_search_class(text, "results");
    Array.from(div_tree.getElementsByClassName(cresults)).forEach(e => {
        e.style.opacity = search.results.opacity;
        e.style.fill = search.results.color;
    });

    const cparents = get_search_class(text, "parents");
    Array.from(div_tree.getElementsByClassName(cparents)).forEach(e => {
        e.style.stroke = search.parents.color;
        e.style.strokeWidth = search.parents.width;
    });

}


function colorize_searches() {
    Object.keys(view.searches).forEach(text => colorize_search(text));
}


// Empty view.searches.
function remove_searches() {
    const texts = Object.keys(view.searches);
    texts.forEach(text => view.searches[text].remove());
}
