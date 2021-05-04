// Functions related to tagging.

import { view, menus } from "./gui.js";

export { tag_node, colorize_tags, remove_tags };


// Tag node with the given name and return true if things went well.
function tag_node(node_id, name) {
    if (!name)
        return false;  // will prevent swal popup from closing

    if (name in view.tags) {
        view.tags[name].nodes.push(node_id);
        colorize_tag(name);
        return true;
    }

    const folder = menus.tags_searches.__folders.tags.addFolder(name);
    const colors = ["#FF0", "#F0F", "#0FF", "#F00", "#0F0", "#00F"].reverse();
    const ntags = Object.keys(view.tags).length;
    view.tags[name] = {
        nodes: [node_id],
        opacity: 0.4,
        color: colors[ntags % colors.length],
    };

    view.tags[name].remove = function() {
        view.tags[name].opacity = view.node.box.opacity;
        view.tags[name].color = view.node.box.color;
        colorize_tag(name);
        delete view.tags[name];
        menus.tags_searches.__folders.tags.removeFolder(folder);
    }

    folder.add(view.tags[name], "opacity", 0, 1).step(0.01).onChange(
        () => colorize_tag(name));
    folder.addColor(view.tags[name], "color").onChange(
        () => colorize_tag(name));

    folder.add(view.tags[name], "remove");

    colorize_tag(name);

    return true;
}


function colorize_tag(name) {
    const tags = view.tags[name];
    tags.nodes.forEach(node_id => {
        const node = document.getElementById("node-" + node_id.join("_"));
        if (node) {
            node.style.opacity = tags.opacity;
            node.style.fill = tags.color;
        }
    });
}


function colorize_tags() {
    Object.keys(view.tags).forEach(name => colorize_tag(name));
}


// Empty view.tags.
function remove_tags() {
    const names = Object.keys(view.tags);
    names.forEach(name => view.tags[name].remove());
}
