// Main file for the gui.

import { init_menus } from "./menu.js";
import { init_events } from "./events.js";
import { update } from "./draw.js";
import { download_newick, download_image, download_svg } from "./download.js";
import { search, remove_searches } from "./search.js";
import { zoom_into_box, zoom_around, zoom_towards_box } from "./zoom.js";
import { draw_minimap, update_minimap_visible_rect } from "./minimap.js";
import { api, api_put, escape_html } from "./api.js";
import { remove_tags } from "./tag.js";
import { remove_collapsed } from "./collapse.js";
import { label_expression, label_property } from "./label.js";

export { view, menus, on_tree_change, on_drawer_change, show_minimap,
         tree_command, get_tid, on_box_click, on_box_wheel, coordinates,
         reset_view, show_help, sort };


// Run main() when the page is loaded.
document.addEventListener("DOMContentLoaded", main);


// Global variables related to the current view on the tree.
// Most will be shown on the top-right gui (using dat.gui).
const view = {
    // tree
    tree: null,  // string with the current tree name
    tree_size: {width: 0, height: 0},
    node_properties: [],  // existing in the current tree
    subtree: "",  // node id of the current subtree; looks like "0,1,0,0,1"
    sorting: {
        sort: () => sort(),
        key: "(dy, dx, name)",
        reverse: false,
    },
    upload: () => window.location.href = "upload_tree.html",
    download: {
        newick: () => download_newick(),
        svg:    () => download_svg(),
        image:  () => download_image(),
    },
    allow_modifications: true,

    // representation
    drawer: {name: "RectLeafNames", type: "rect", npanels: 1},  // default drawer
    min_size: 15,  // for less pixels, the drawer will collapse things
    label_expression: () => label_expression(),
    label_property: () => label_property(),
    current_property: "name",  // pre-selected property in the add label menu
    labels: {},  // will contain the labels created
    rmin: 0,
    angle: {min: -180, max: 180},
    align_bar: 80,  // % of the screen width where the aligned panel starts
    collapsed_ids: {},

    // searches
    search: () => search(),
    searches: {},  // will contain the searches done

    // tags
    tags: {},  // will contain the tagged nodes

    // info
    nnodes: 0,  // number of visible nodeboxes
    tnodes: 0,  // number of total nodeboxes
    tleaves: 0,  // number of total leaves (outer nodeboxes)
    pos: {cx: 0, cy: 0},  // in-tree current pointer position
    show_tree_info: () => show_tree_info(),

    // view
    reset_view: () => reset_view(),
    tl: {x: null, y: null},  // top-left of the view (in tree coordinates)
    zoom: {x: null, y: null},  // initially chosen depending on the tree size
    select_text: false,  // if true, clicking and moving the mouse selects text

    // style
    node: {
        box: {
            opacity: 0,
            color: "#222",
        },
        dot: {
            radius: 2,
            opacity: 1,
        },
    },
    outline: {
        opacity: 0.1,
        color: "#A50",
        width: 0.5,
        slanted: true,
    },
    line: {
        length: {
            color: "#000",
            width: 1,
        },
        children: {
            color: "#000",
            width: 1,
            pattern: "dotted",
        },
    },
    array: {padding: 0.0},
    font_sizes: {auto: true, scroller: undefined, fixed: 10},

    name: {  // this may go away if we can do names nicely with labels
        color: "#00A",
        font: "sans-serif",
        max_size: 25,
        padding: {left: 10, vertical: 0.20},
    },

    // minimap
    minimap: {
        show: true,
        uptodate: false,
        width: 10,
        height: 40,
        zoom: {x: 1, y: 1},
    },

    smart_zoom: true,

    share_view: () => share_view(),

    show_help: () => show_help(),
};

const menus = {  // will contain the menus on the top
    main: undefined,
    representation: undefined,
    tags_searches: undefined,
};

const trees = {};  // will translate names to ids (trees[tree_name] = tree_id)


async function main() {
    await init_trees();

    await set_query_string_values();

    reset_node_count();

    const drawers = await api("/drawers");
    init_menus(menus, Object.keys(trees), drawers);

    init_events();

    store_node_properties();

    draw_minimap();
    show_minimap("visible");

    update();

    const sample_trees = ["ncbi", "GTDB_bact_r95"];  // hardcoded for the moment
    view.allow_modifications = !sample_trees.includes(view.tree);
}


// Fill global var trees, which translates tree names into their database ids.
async function init_trees() {
    const trees_info = await api("/trees");

    trees_info.forEach(t => trees[t.name] = t.id);  // like trees["mytree"] = 7
}


// Return current (sub)tree id (its id number followed by its subtree id).
function get_tid() {
    if (view.tree in trees) {
        return trees[view.tree] + (view.subtree ? "," + view.subtree : "");
    }
    else {
        Swal.fire({
            html: `Cannot find tree ${escape_html(view.tree)}<br><br>
                   Opening a default tree.`,
            icon: "error",
        });

        view.tree = Object.keys(trees)[0];  // select a default tree
        on_tree_change();

        return trees[view.tree];
    }
}


// Perform an action on a tree (among the available in the API as PUT calls).
async function tree_command(command, params=undefined) {
    try {
        await api_put(`/trees/${get_tid()}/${command}`, params);

        const commands_modifying_size = ["root_at", "remove"];
        if (commands_modifying_size.includes(command))
            view.tree_size = await api(`/trees/${get_tid()}/size`);
    }
    catch (ex) {
        Swal.fire({
            title: "Command Error",
            html: `When running <tt>${command}</tt>:<br><br>${ex.message}`,
            icon: "error",
        });
    }
}


// What happens when the user selects a new tree in the menu.
async function on_tree_change() {
    if (!menus.main)
        return;  // we haven't initialized yet!

    div_tree.style.cursor = "wait";
    remove_searches();
    remove_collapsed();
    remove_tags();
    view.tree_size = await api(`/trees/${get_tid()}/size`);
    store_node_properties();
    reset_node_count();
    reset_zoom();
    reset_position();
    draw_minimap();
    update();

    const sample_trees = ["ncbi", "GTDB_bact_r95"];  // hardcoded for the moment
    view.allow_modifications = !sample_trees.includes(view.tree);
}


// What happens when the user selects a new drawer in the menu.
async function on_drawer_change() {
    const previous_type = view.drawer.type;

    const drawer_info = await api(`/drawers/${view.drawer.name}`);
    view.drawer.type = drawer_info.type;
    view.drawer.npanels = drawer_info.npanels;

    if (drawer_info.type === "rect" && drawer_info.npanels > 1)
        div_aligned.style.display = "initial";  // show aligned panel
    else
        div_aligned.style.display = "none";  // hide aligned panel

    if (drawer_info.type !== previous_type) {
        reset_zoom();
        reset_position();
        draw_minimap();
    }

    update();
}


// Save the available node properties in view.node_properties and the drop-down
// list of the menu that allows to label based on properties.
async function store_node_properties() {
    const properties_extra = await api(`/trees/${get_tid()}/properties`);

    view.node_properties = ["name", "length"].concat(properties_extra);

    const select = menus.representation
        .__folders.labels.__folders.add.__folders.properties
        .__controllers[0].__select;  // drop-down list

    while (select.length > 0)  // remove properties that may be in the list
        select.remove(select.length - 1);

    for (const p of view.node_properties) {  // add new properties to the list
        const opt = document.createElement("option");
        opt.value = opt.text = p;
        select.add(opt);
    }

    view.current_property = "name";
}


function reset_view() {
    reset_zoom();
    reset_position();
    if (!view.minimap.uptodate)
        draw_minimap();
    update();
}


// Set values that have been given with the query string.
async function set_query_string_values() {
    const unknown_params = [];
    const params = new URLSearchParams(location.search);

    for (const [param, value] of params) {
        if (param === "tree")
            view.tree = value;
        else if (param === "subtree")
            view.subtree = value;
        else if (param === "x")
            view.tl.x = Number(value);
        else if (param === "y")
            view.tl.y = Number(value);
        else if (param === "w")
            view.zoom.x = div_tree.offsetWidth / Number(value);
        else if (param === "h")
            view.zoom.y = div_tree.offsetHeight / Number(value);
        else if (param === "drawer")
            view.drawer.name = value;
        else
            unknown_params.push(param);
    }

    if (unknown_params.length > 0) {
        const pars = unknown_params.map(t => `<tt>${escape_html(t)}</tt>`);
        Swal.fire({
            title: "Oops!",
            html: "Unknown parameters passed in url:<br><br>" + pars.join(", "),
            icon: "warning",
        });
    }

    await set_consistent_values();
}

async function set_consistent_values() {
    if (view.tree === null)
        view.tree = Object.keys(trees)[0];  // select default tree

    view.tree_size = await api(`/trees/${get_tid()}/size`);

    let drawer_info;
    try {
        drawer_info = await api(`/drawers/${view.drawer.name}`);
    }
    catch (ex) {
        Swal.fire({
            html: `Cannot find drawer ${escape_html(view.drawer.name)}<br><br>
                   Opening a default drawer.`,
            icon: "error",
        });
        view.drawer.name = "Rect";
        drawer_info = {"type": "rect", "npanels": 1};
    }

    view.drawer.type = drawer_info.type;  // "rect" or "circ"
    view.drawer.npanels = drawer_info.npanels;  // if > 1, there's aligned stuff

    if (drawer_info.type === "rect" && drawer_info.npanels > 1)
        div_aligned.style.display = "initial";  // show div for aligned content
    else
        div_aligned.style.display = "none";     // hide div for aligned content

    if (view.drawer.type === "circ") {  // adjust zoom nicely so zx == zy
        if (view.zoom.x !== null && view.zoom.y !== null)
            view.zoom.x = view.zoom.y = Math.min(view.zoom.x, view.zoom.y);
        else if (view.zoom.x !== null)
            view.zoom.y = view.zoom.x;
        else if (view.zoom.y !== null)
            view.zoom.x = view.zoom.y;
    }

    reset_zoom(view.zoom.x === null, view.zoom.y === null);
    reset_position(view.tl.x === null, view.tl.y === null);
}


function show_minimap(show) {
    const status = (show ? "visible" : "hidden");
    div_minimap.style.visibility = div_visible_rect.style.visibility = status;
    if (show) {
        if (!view.minimap.uptodate)
            draw_minimap();
        update_minimap_visible_rect();
    }
}


function reset_node_count() {
    api(`/trees/${get_tid()}/nodecount`).then(n => {
        view.tnodes = n.tnodes;
        view.tleaves = n.tleaves;
    });
}


// Set the zoom so the full tree fits comfortably on the screen.
function reset_zoom(reset_zx=true, reset_zy=true) {
    if (!(reset_zx || reset_zy))
        return;

    const size = view.tree_size;

    if (view.drawer.type === "rect") {
        if (reset_zx)
            view.zoom.x = 0.6 * div_tree.offsetWidth / size.width;
        if (reset_zy)
            view.zoom.y = 0.9 * div_tree.offsetHeight / size.height;
    }
    else if (view.drawer.type === "circ") {
        const min_w_h = Math.min(div_tree.offsetWidth, div_tree.offsetHeight);
        view.zoom.x = view.zoom.y = min_w_h / (view.rmin + size.width) / 2;
    }
}


function reset_position(reset_x=true, reset_y=true) {
    if (view.drawer.type === "rect") {
        if (reset_x)
            view.tl.x = -0.10 * div_tree.offsetWidth / view.zoom.x;
        if (reset_y)
            view.tl.y = -0.05 * div_tree.offsetHeight / view.zoom.y;
    }
    else if (view.drawer.type === "circ") {
        if (!(view.angle.min === -180 && view.angle.max === 180)) {
            view.angle.min = -180;
            view.angle.max = 180;
            view.minimap.uptodate = false;
        }
        if (reset_x)
            view.tl.x = -div_tree.offsetWidth / view.zoom.x / 2;
        if (reset_y)
            view.tl.y = -div_tree.offsetHeight / view.zoom.y / 2;
    }
}


// Return an url with the view of the given rectangle of the tree.
function get_url_view(x, y, w, h) {
    const qs = new URLSearchParams({
        x: x, y: y, w: w, h: h,
        tree: view.tree, subtree: view.subtree, drawer: view.drawer.name,
    }).toString();
    return window.location.origin + window.location.pathname + "?" + qs;
}


// Show an alert with information about the current tree and view.
async function show_tree_info() {
    const info = await api(`/trees/${get_tid()}`);

    const props = view.node_properties.map(p =>
        `<tt>${escape_html(p)}</tt>`).join("<br>");

    const w = div_tree.offsetWidth / view.zoom.x,
          h = div_tree.offsetHeight / view.zoom.y;
    const url = get_url_view(view.tl.x, view.tl.y, w, h);

    const result = await Swal.fire({
        title: "Tree Information",
        icon: "info",
        html: `<b>Name</b>: ${escape_html(info.name)}<br><br>` +
            (info.description ? `${info.description}<br><br>` : "") +
            `Node properties:<br>${props}<br><br>` +
            `(<a href="${url}">current view</a>)`,
        confirmButtonText: navigator.clipboard ? "Copy view to clipboard" : "Ok",
        showCancelButton: true,
    });

    if (result.isConfirmed && navigator.clipboard)
        navigator.clipboard.writeText(url);
}


// Open a dialog with a link to the current view of the tree.
// It is either copied to the clipboard (if possible), or shown as a link.
// The link can be opened in a different browser by someone else and they
// would see the same part of the same tree.
function share_view() {
    const w = div_tree.offsetWidth / view.zoom.x,
          h = div_tree.offsetHeight / view.zoom.y;
    const url = get_url_view(view.tl.x, view.tl.y, w, h);

    if (navigator.clipboard) {
        navigator.clipboard.writeText(url);
        Swal.fire({
            text: "Current view has been copied to the clipboard.",
            icon: "success",
        });
    }
    else {
        Swal.fire({
            html: "Right-click on link to copy to the clipboard:<br><br>" +
                  `(<a href="${url}">current tree view</a>)`,
        });
    }
}


function show_help() {
    const help_text = `
<table style="margin: 0 auto">
<thead><tr><th>General Instructions</th></tr></thead>
<tbody style="text-align: left">
<tr><td><br>
Click and drag with the left mouse button to move around the tree.
</td></tr>
<tr><td><br>
Use the mouse wheel to zoom in and out. Press <kbd>Ctrl</kbd> or <kbd>Alt</kbd>
while using the wheel to zoom differently.
</td></tr>
<tr><td><br>
Click on the minimap to go to a different area or drag the current view.
</td></tr>
<tr><td><br>
Right-click on a node to show options to interact with it.
</td></tr>
<tr><td><br>
Use the options in the menu at the top right to change the visualization.
</td></tr>
</tbody>
</table>

<br>
<br>

<table style="margin: 0 auto">
<thead><tr><th colspan="2">Keyboard Shortcuts</th></tr></thead>
<tbody>
<tr><td> </td><td>&nbsp; </td></tr>
<tr><td><kbd>F1</kbd></td><td style="text-align: left">&nbsp; help</td></tr>
<tr><td><kbd>/</kbd></td><td style="text-align: left">&nbsp; search</td></tr>
<tr><td><kbd>r</kbd></td><td style="text-align: left">&nbsp; reset view</td></tr>
<tr><td><kbd>m</kbd></td><td style="text-align: left">&nbsp; toggle minimap</td></tr>
<tr><td><kbd>⬅️</kbd> <kbd>➡️</kbd> <kbd>⬆️</kbd> <kbd>⬇️</kbd></td>
    <td style="text-align: left">&nbsp; move the view</td></tr>
<tr><td><kbd>+</kbd> <kbd>&ndash;</kbd></td>
    <td style="text-align: left">&nbsp; zoom in / out</td></tr>
</tbody>
</table>

<br>

<hr>

<br>

<div style="font-size: 0.8em">
<p>
<img src="icon.png" alt="ETE Toolkit logo">
Tree Explorer is part of the
<a href="http://etetoolkit.org/">ETE Toolkit</a>.
</p>

<p>
<img src="https://chanzuckerberg.com/wp-content/themes/czi/img/logo.svg"
     width="50" alt="Chan Zuckerberg Initiative logo">
Smart visualization funded by
<a href="https://chanzuckerberg.com/">CZI</a>.
</p>
</div>

<br>
<br>
`;
    Swal.fire({
        title: "Tree Explorer",
        html: help_text,
        icon: "info",
    });
}


// Return the corresponding in-tree position of the given point (on the screen).
function coordinates(point) {
    const x = view.tl.x + point.x / view.zoom.x,
          y = view.tl.y + point.y / view.zoom.y;

    if (view.drawer.type === "rect") {
        return [x, y];
    }
    else if (view.drawer.type === "circ") {
        const r = Math.sqrt(x*x + y*y);
        const a = Math.atan2(y, x) * 180 / Math.PI;
        return [r, a];
    }
}


function on_box_click(event, box, node_id) {
    if (event.detail === 2 || event.ctrlKey) {  // double-click or ctrl-click
        zoom_into_box(box);
    }
    else if (event.shiftKey) {  // shift-click
        view.subtree += (view.subtree ? "," : "") + node_id;
        on_tree_change();
    }
}


// Mouse wheel -- zoom in/out (instead of scrolling).
function on_box_wheel(event, box) {
    event.preventDefault();

    const point = {x: event.pageX, y: event.pageY};
    const zoom_in = event.deltaY < 0;
    const do_zoom = {x: !event.ctrlKey, y: !event.altKey};

    if (view.drawer.type === "rect" && view.smart_zoom)
        zoom_towards_box(box, point, zoom_in, do_zoom);
    else
        zoom_around(point, zoom_in, do_zoom);
}


async function sort(node_id=[]) {
    if (view.allow_modifications) {
        await tree_command("sort",
                           [node_id, view.sorting.key, view.sorting.reverse]);
        draw_minimap();
        update();
    }
    else {
        Swal.fire({
            html: "Sorry, sorting is disabled for this tree. But you can try " +
                  "it on your own uploaded trees!",
            icon: "info",
        });
    }
}
