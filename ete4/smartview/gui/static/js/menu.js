// Functions related to the top-right menus.

import { view, on_tree_change, on_drawer_change, show_minimap } from "./gui.js";
import { draw_minimap } from "./minimap.js";
import { update } from "./draw.js";

export { init_menus };


// Init the menus on the top with all the options we can see and change.
function init_menus(menus, trees, drawers) {
    menus.main = create_menu_main(trees);
    menus.representation = create_menu_representation(drawers);
    menus.tags_searches = create_menu_tags_searches();
}


function create_menu_main(trees) {
    const menu = new dat.GUI({autoPlace: false, closeOnTop: true});
    div_menu_main.appendChild(menu.domElement);

    add_folder_tree(menu, trees);

    add_folder_info(menu);

    add_folder_view(menu);

    add_folder_minimap(menu);

    menu.add(view, "smart_zoom").name("smart zoom");
    menu.add(view, "share_view").name("share view");
    menu.add(view, "show_help").name("help");

    return menu;
}


function create_menu_representation(drawers) {
    const menu = new dat.GUI({autoPlace: false, closeOnTop: true});
    menu.close();
    div_menu_representation.appendChild(menu.domElement);

    menu.add(view.drawer, "name", drawers).name("drawer").onChange(
        on_drawer_change);

    menu.add(view, "min_size", 1, 100).name("collapse at").onChange(
        update);

    const folder_circ = menu.addFolder("circular");

    function update_with_minimap() {
        draw_minimap();
        update();
    }
    folder_circ.add(view, "rmin").name("radius min").onChange(
        update_with_minimap);
    folder_circ.add(view.angle, "min", -180, 180).name("angle min").onChange(
        update_with_minimap);
    folder_circ.add(view.angle, "max", -180, 180).name("angle max").onChange(
        update_with_minimap);

    add_folder_style(menu);

    const folder_labels = menu.addFolder("labels");

    const folder_add = folder_labels.addFolder("add");

    const folder_properties = folder_add.addFolder("properties");

    folder_properties.add(view, "current_property", view.node_properties).name("properties");
    folder_properties.add(view, "label_property").name("add property");

    const folder_expressions = folder_add.addFolder("expressions");

    folder_expressions.add(view, "label_expression").name("add expression");

    return menu;
}


function create_menu_tags_searches() {
    const menu = new dat.GUI({autoPlace: false, closeOnTop: true});
    menu.close();
    div_menu_tags_searches.appendChild(menu.domElement);

    menu.addFolder("collapsed");  // filled dynamically

    menu.addFolder("tags");  // filled dynamically with tag_node()

    add_folder_searches(menu);

    return menu;
}


function add_folder_tree(menu, trees) {
    const folder_tree = menu.addFolder("tree");

    folder_tree.add(view, "tree", trees).onChange(() => {
        view.subtree = "";
        on_tree_change();
    });
    folder_tree.add(view, "subtree").onChange(on_tree_change);

    const folder_sort = folder_tree.addFolder("sort");
    folder_sort.add(view.sorting, "sort");
    folder_sort.add(view.sorting, "key");
    folder_sort.add(view.sorting, "reverse");

    folder_tree.add(view, "upload");

    const folder_download = folder_tree.addFolder("download");
    folder_download.add(view.download, "newick");
    folder_download.add(view.download, "svg");
    folder_download.add(view.download, "image");
}


function add_folder_searches(menu) {
    const folder_searches = menu.addFolder("searches");

    folder_searches.add(view, "search").name("new search");
}


function add_folder_info(menu) {
    const folder_info = menu.addFolder("info");

    folder_info.add(view, "nnodes").name("visible nodes").listen();
    folder_info.add(view, "tnodes").name("total nodes").listen();
    folder_info.add(view, "tleaves").name("total leaves").listen();
    folder_info.add(view.pos, "cx").step(0.001).listen();
    folder_info.add(view.pos, "cy").step(0.001).listen();
    folder_info.add(view, "show_tree_info").name("show details");
}


function add_folder_view(menu) {
    const folder_view = menu.addFolder("view");

    folder_view.add(view, "reset_view").name("reset view");

    const folder_tl = folder_view.addFolder("top-left");
    folder_tl.add(view.tl, "x").step(0.001).onChange(update);
    folder_tl.add(view.tl, "y").step(0.001).onChange(update);

    const folder_zoom = folder_view.addFolder("zoom");
    folder_zoom.add(view.zoom, "x").step(0.001).onChange(update);
    folder_zoom.add(view.zoom, "y").step(0.001).onChange(update);

    const folder_aligned = folder_view.addFolder("align bar");
    folder_aligned.add(view, "align_bar", 0, 100).name("position").onChange(
        (value) => div_aligned.style.width = `${100 - value}%`);

    folder_view.add(view, "select_text").name("select text").onChange(() => {
        style("font").userSelect = (view.select_text ? "text" : "none");
        div_tree.style.cursor = (view.select_text ? "text" : "auto");
        div_aligned.style.cursor = (view.select_text ? "text" : "ew-resize");
        set_boxes_clickable(!view.select_text);
    });
}

function set_boxes_clickable(clickable) {
    const value = clickable ? "auto" : "none";
    Array.from(div_tree.getElementsByClassName("box")).forEach(
        e => e.style.pointerEvents = value);
}


function add_folder_style(menu) {
    const folder_style = menu.addFolder("style");

    const folder_node = folder_style.addFolder("node");

    const folder_box = folder_node.addFolder("box");

    folder_box.add(view.node.box, "opacity", 0, 0.2).step(0.001).onChange(
        () => style("node").opacity = view.node.box.opacity);
    folder_box.addColor(view.node.box, "color").onChange(
        () => style("node").fill = view.node.box.color);

    const folder_dot = folder_node.addFolder("dot");

    folder_dot.add(view.node.dot, "radius", 0, 10).step(0.1).onChange(() =>
        Array.from(div_tree.getElementsByClassName("nodedot")).forEach(
            e => e.setAttribute("r", view.node.dot.radius)));

    folder_dot.add(view.node.dot, "opacity", 0, 1).step(0.01).onChange(
        () => style("nodedot").opacity = view.node.dot.opacity);

    const folder_outline = folder_style.addFolder("outline");

    folder_outline.add(view.outline, "opacity", 0, 1).step(0.1).onChange(
        () => style("outline").fillOpacity = view.outline.opacity);
    folder_outline.addColor(view.outline, "color").onChange(
        () => style("outline").fill = view.outline.color);
    folder_outline.add(view.outline, "width", 0.1, 10).onChange(
        () => style("outline").strokeWidth = view.outline.width);
    folder_outline.add(view.outline, "slanted").onChange(() => {
        update();
        draw_minimap();
    });

    const folder_lines = folder_style.addFolder("lines");

    const folder_length = folder_lines.addFolder("length");

    folder_length.addColor(view.line.length, "color").onChange(
        () => style("lengthline").stroke = view.line.length.color);
    folder_length.add(view.line.length, "width", 0.1, 10).onChange(
        () => style("lengthline").strokeWidth = view.line.length.width);

    const folder_children = folder_lines.addFolder("children");

    folder_children.addColor(view.line.children, "color").onChange(
        () => style("childrenline").stroke = view.line.children.color);
    folder_children.add(view.line.children, "width", 0.1, 10).onChange(
        () => style("childrenline").strokeWidth = view.line.children.width);
    folder_children.add(view.line.children, "pattern",
        ["solid", "dotted", "dotted - 2", "dotted - 4"])
        .onChange(() => {
            const pattern = view.line.children.pattern;
            if (pattern === "solid")
                style("childrenline").strokeDasharray = "";
            else if (pattern === "dotted")
                style("childrenline").strokeDasharray = "1";
            else if (pattern === "dotted - 2")
                style("childrenline").strokeDasharray = "2";
            else if (pattern === "dotted - 4")
                style("childrenline").strokeDasharray = "4";
        });

    const folder_text = folder_style.addFolder("text");

    const folder_name = folder_text.addFolder("name");

    folder_name.addColor(view.name, "color").onChange(
        () => style("name").fill = view.name.color);

    const folder_padding = folder_name.addFolder("padding");

    folder_padding.add(view.name.padding, "left", -20, 200).onChange(update);
    folder_padding.add(view.name.padding, "vertical", 0, 1).step(0.01).onChange(
        update);
    folder_name.add(view.name, "font", ["sans-serif", "serif", "monospace"])
        .onChange(() => style("name").fontFamily = view.name.font);
    folder_name.add(view.name, "max_size", 1, 200).name("max size").onChange(
        update);

    folder_text.add(view.font_sizes, "auto").name("automatic size").onChange(
        () => {
            style("font").fontSize =
                view.font_sizes.auto ? "" : `${view.font_sizes.fixed}px`;

            if (view.font_sizes.auto && view.font_sizes.scroller)
                view.font_sizes.scroller.remove();
            else
                view.font_sizes.scroller = create_font_size_scroller();
    });

    function create_font_size_scroller() {
        return folder_text.add(view.font_sizes, "fixed", 0.1, 50).onChange(
            () => style("font").fontSize = `${view.font_sizes.fixed}px`);
    }

    const folder_array = folder_style.addFolder("array");

    folder_array.add(view.array, "padding", 0, 1).step(0.01).onChange(
        update);
}


function style(name) {
    const pos = {
        "line": 1,
        "lengthline": 2,
        "childrenline": 3,
        "nodedot": 4,
        "font": 6,
        "name": 7,
        "node": 8,
        "outline": 9,
    };
    return document.styleSheets[0].cssRules[pos[name]].style;
}


function add_folder_minimap(menu) {
    const folder_minimap = menu.addFolder("minimap");

    folder_minimap.add(view.minimap, "width", 0, 100).onChange(() => {
        if (view.drawer.type === "circ") {
            view.minimap.height = view.minimap.width * div_tree.offsetWidth
                                                     / div_tree.offsetHeight;
            menu.updateDisplay();
        }
        draw_minimap();
    });
    folder_minimap.add(view.minimap, "height", 0, 100).onChange(() => {
        if (view.drawer.type === "circ") {
            view.minimap.width = view.minimap.height * div_tree.offsetHeight
                                                     / div_tree.offsetWidth;
            menu.updateDisplay();
        }
        draw_minimap();
    });
    folder_minimap.add(view.minimap, "show").onChange(show_minimap);
}
