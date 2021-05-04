// Functions related to labels.

import { view, menus } from "./gui.js";
import { draw_tree, get_class_name } from "./draw.js";

export { label_expression, label_property, colorize_labels };


// Put a label in the nodes and redraw the tree (with the new label too).
async function label_expression() {
    const result = await Swal.fire({
        input: "text",
        position: "top-end",
        inputPlaceholder: "Enter expression",
        showConfirmButton: false,
        preConfirm: text => {
            if (!text)
                return false;
        },
    });

    if (result.isConfirmed) {
        add_label_to_menu(result.value);
        draw_tree();
    }
}


function label_property() {
    const prop = view.current_property;

    if (prop === "name" || prop === "length")
        add_label_to_menu(prop);
    else
        add_label_to_menu(`p.get('${prop}', '')`);

    draw_tree();
}


function add_label_to_menu(expression) {
    const folder_labels = menus.representation.__folders.labels;

    if (expression in folder_labels.__folders) {
        Swal.fire({
            html: "Label already exists", icon: "warning", timer: 5000,
            toast: true, position: "top-end",
        });
        return;
    }

    const folder = folder_labels.addFolder(expression);

    const colors = ["#0A0", "#A00", "#00A", "#550", "#505", "#055", "#000"];
    const nlabels = Object.keys(view.labels).length;

    view.labels[expression] = {
        nodetype: "any",
        position: "branch-top",
        color: colors[nlabels % colors.length],
        font: "sans-serif",
        max_size: 15,
    }

    view.labels[expression].remove = function() {
        delete view.labels[expression];
        folder_labels.removeFolder(folder);
        draw_tree();
    }

    const label = view.labels[expression];

    folder.add(label, "nodetype", ["leaf", "internal", "any"])
        .onChange(draw_tree);

    const positions = ["branch-top", "branch-bottom", "branch-top-left",
        "branch-bottom-left","float"];
    folder.add(label, "position", positions).onChange(draw_tree);

    folder.addColor(label, "color").onChange(
        () => colorize_label(expression));

    folder.add(label, "font",
        ["sans-serif", "serif", "monospace"]).onChange(
        () => colorize_label(expression));

    folder.add(label, "max_size", 1, 100).name("max size")
        .onChange(draw_tree);

    folder.add(label, "remove");
}


function colorize_label(expression) {
    const label = view.labels[expression];

    const clabel = get_class_name("label_" + expression);
    Array.from(div_tree.getElementsByClassName(clabel)).forEach(e => {
        e.style.fill = label.color;
        e.style.fontFamily = label.font;
    });
}


function colorize_labels() {
    Object.keys(view.labels).forEach(expression => colorize_label(expression));
}
