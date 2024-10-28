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

export { view, menus, on_tree_change, on_shape_change, show_minimap,
         tree_command, get_tid, on_box_click, on_box_wheel, coordinates,
         reset_view, show_help, sort, to_opts, set_tree_style };


// Run main() when the page is loaded.
document.addEventListener("DOMContentLoaded", main);


// Global variables related to the current view on the tree.
// Most will be shown on the menu.
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
    upload: () => window.location.href = "upload.html",
    download: {
        newick: () => download_newick(),
        svg:    () => download_svg(),
        image:  () => download_image(),
    },
    allow_modifications: true,

    // representation
    shape: "rectangular",  // default shape
    node_height_min: 30,  // for less pixels, we will collapse nodes
    content_height_min: 4,  // for less pixels, node contents won't be drawn
    rmin: 0,
    angle: {min: -180, max: 180},
    align_bar: 80,  // % of the screen width where the aligned panel starts
    collapsed_ids: {},

    // layouts
    layouts: {},  // will contain available layouts and say if they are active

    // labels
    label_expression: () => label_expression(),
    label_property: () => label_property(),
    current_property: "name",  // pre-selected property in the add label menu
    labels: new Map(),  // will contain the labels created

    // searches
    search: () => search(),
    searches: {},  // will contain the searches done

    // tags
    tags: {},  // will contain the tagged nodes

    // info
    nnodes_visible: 0,  // number of visible nodes
    nnodes: 0,  // number of total nodes in tree
    nleaves: 0,  // number of total leaves in tree
    pos: {cx: 0, cy: 0},  // in-tree current pointer position
    show_tree_info: () => show_tree_info(),

    // view
    reset_view: () => reset_view(),
    tl: {x: null, y: null},  // top-left of the view (in tree coordinates)
    zoom: {x: null, y: null},  // initially chosen depending on the tree size
    select_text: false,  // if true, clicking and moving the mouse selects text

    // style
    default_rules: null,  // will contain an array of the original css rules
    node: {
        box: {
            opacity: 1,
            fill: "#FFF",
        },
        dot: {
            shape: "circle",
            radius: 2,
            opacity: 0.5,
            fill: "#00F",
        },
    },
    collapsed: {
        shape: "skeleton",
        opacity: 0.1,
        stroke: "#A50",
        "stroke-width": 0.4,
    },
    hz_line: {
        stroke: "#000",
        "stroke-width": 0.5,
    },
    vt_line: {
        stroke: "#000",
        "stroke-width": 0.5,
        pattern: "solid",
    },
    array: {padding: 0.0},
    font_sizes: {auto: true, scroller: undefined, fixed: 10},

    // minimap
    minimap: {
        show: false,
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
    pane: undefined,  // main pane containing the tabs
    layouts: undefined,  // to show the available layouts (and (de)activate them)
    labels: undefined,  // see labels.js
    node_properties: undefined,  // for labels based on properties (see below)
    collapsed: undefined,  // for manually collapsed nodes (see collapse.js)
    selections: undefined,  // see tag.js
    searches: undefined,  // see search.js
};

const trees = {};  // will translate names to ids (trees[tree_name] = tree_id)


async function main() {
    try {
        save_default_rules();

        await init_trees();

        await set_query_string_values();

        init_menus(Object.keys(trees));

        await populate_layouts();

        await set_tree_style();

        await set_consistent_values();

        reset_node_count();

        init_events();

        store_node_properties();

        draw_minimap();
        show_minimap(false);  // set to true to have a minimap at startup

        update();

        const sample_trees = [];
        // NOTE: We could add here trees like "GTDB_bact_r95" to have a public
        // server showing the trees but not letting modifications on them.
        view.allow_modifications = !sample_trees.includes(view.tree);
    }
    catch (ex) {
        Swal.fire({html: ex.message, icon: "error"});
    }
}


// Save the CSS rules from the main stylesheet, to be able to restore later.
function save_default_rules() {
    if (view.default_rules)
        return;  // default css rules already saved!

    const rules = document.styleSheets[0].cssRules;
    view.default_rules = Array.from(rules).map(r => r.cssText);
    view.default_rules.reverse();  // so we can easily insert them later
}


// Fill global var trees, which translates tree names into their ids.
async function init_trees() {
    const trees_info = await api("/trees");

    trees_info.forEach(t => trees[t.name] = t.id);
    // NOTE: It used to be associations like  trees["mytree"] = 7  where
    // the 7 was the id in the database. Now they are more like
    // tree["mytree"] = "mytree"  so we may want to get rid of them.
}


// Return current (sub)tree id (its id followed by its subtree id).
// NOTE: view.tree (the tree name) should not contain "," for this to work.
function get_tid() {
    if (view.tree in trees) {
        return trees[view.tree] + (view.subtree ? "," + view.subtree : "");
    }
    else {
        Swal.fire({
            html: `Cannot find tree ${escape_html(view.tree)}<br><br>
                   Opening first stored tree.`,
            icon: "error",
        });

        view.tree = Object.keys(trees)[0];  // select a default tree
        on_tree_change();

        return trees[view.tree];
    }
}


// Set some style values according to the active layouts.
async function set_tree_style() {
    // Find the active layouts and request their combined tree style.
    const active = JSON.stringify(Object.entries(view.layouts)
        .filter( ([name, status]) => status["active"] )
        .map( ([name, status]) => name ));

    const qs = new URLSearchParams({"active": active}).toString();

    const style = await api(`/trees/${get_tid()}/style?${qs}`);  // ask backend

    // We set the defaults first, and then override with the server's response.

    // Set rectangular or circular shape.
    view.shape = "rectangular";
    if ("shape" in style) {
        if (! ["rectangular", "circular"].includes(style.shape))
            throw new Error(`unknown shape "${style.shape}"`);
        view.shape = style.shape;
    }

    // Set collapse and visualize sizes.
    view.node_height_min = 30;
    if ("node-height-min" in style)
        view.node_height_min = style["node-height-min"];

    view.content_height_min = 4;
    if ("content-height-min" in style)
        view.content_height_min = style["content-height-min"];

    // Set limits.
    view.rmin = 0;
    if ("radius" in style)
        view.rmin = style.radius;

    view.angle.min = -180;
    if ("angle-start" in style)
        view.angle.min = style["angle-start"];

    view.angle.max = 180;
    if ("angle-end" in style)
        view.angle.max = style["angle-end"];

    if ("angle-span" in style)
        if ("angle-start" in style)
            view.angle.max = view.angle.min + style["angle-span"];
        else
            view.angle.min = view.angle.max - style["angle-span"];

    // Get special (non-css) styles first and remove them.
    view.node.dot.shape = "circle";
    view.node.dot.radius = 2;
    if ("dot" in style) {
        const shape = style.dot.shape;
        if (shape !== undefined) {
            if (! (typeof shape === "number") &&
                ! ["none", "circle", "triangle", "square", "pentagon",
                   "hexagon", "heptagon", "octogon"].includes(shape))
                throw new Error(`unknown dot shape ${shape}`);
            view.node.dot.shape = shape;
            delete style.dot.shape;  // so we don't use it later
        }

        const radius = style.dot.radius;
        if (radius !== undefined) {
            view.node.dot.radius = radius;
            delete style.dot.radius;  // so we don't use it later
        }
    }

    view.collapsed.shape = "skeleton";
    if ("collapsed" in style && "shape" in style.collapsed) {
        if (! ["skeleton", "outline"].includes(style.collapsed.shape))
            throw new Error(`unknown collapsed shape "${style.collapsed.shape}"`);
        view.collapsed.shape = style.collapsed.shape;
        delete style.collapsed.shape;  // so we don't use it later
    }

    // Update styles for general node graphical elements.
    while (document.styleSheets[0].cssRules.length > 0)
        document.styleSheets[0].deleteRule(0);
    view.default_rules.forEach(r => document.styleSheets[0].insertRule(r));
    // Iterate over name of elements whose style we can change, their position
    // pos in CSS rules (in gui.css), and the global variable that tracks them.
    for (const [name, pos, gvar] of
             [["box", 7, view.node.box],
              ["collapsed", 8, view.collapsed],
              ["dot", 4, view.node.dot],
              ["hz-line", 2, view.hz_line],
              ["vt-line", 3, view.vt_line]]) {
        if (name in style) {
            // Update global variables (exposed in the menus).
            Object.entries(style[name]).forEach( ([k, v]) => gvar[k] = v );

            // Update CSS rules.
            document.styleSheets[0].cssRules[pos].style.cssText +=
                Object.entries(style[name]).map( ([k, v]) => `${k}: ${v}` )
                .join("; ");
        }
    }

    if ("aliases" in style) {
        // Add new stylesheet with all the ns_* names for the styles.
        // They will be used when elements with those styles appear in draw.js
        const sheet = new CSSStyleSheet();
        for (const name in style["aliases"]) {
            const block = Object.entries(style["aliases"][name])
                .map( ([prop, value]) => `${prop}: ${value}` ).join("; ");
            sheet.insertRule(`.ns_${name} { ${block} }`);
        }
        document.adoptedStyleSheets = [sheet];
    }
    else {
        document.adoptedStyleSheets = [];
    }
}


// Fill the folder menus.layouts with the actual available layouts.
async function populate_layouts() {
    // First clear the existing layouts from the menu.
    for (const layout of menus.layouts.children) {
        menus.layouts.remove(layout);
    }

    // Get list of existing layouts for the current tree and populate the menu.
    const layouts = await api(`/trees/${get_tid()}/layouts`);

    for (const name in layouts) {
        view.layouts[name] = {active: layouts[name]["active"]};
        menus.layouts.addBinding(view.layouts[name], "active", {label: name})
            .on("change", async () => {
                await set_tree_style();
                update();
            });
    }
}


// Perform an action on a tree (among the available in the API as PUT calls).
async function tree_command(command, params=undefined) {
    try {
        await api_put(`/trees/${get_tid()}/${command}`, params);

        const commands_modifying_size = [  // possibly modifying it at least
            "set_outgroup", "remove", "edit", "to_ultrametric", "to_dendrogram"
        ];
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
    if (!menus.pane)
        return;  // we haven't initialized yet!

    div_tree.style.cursor = "wait";
    remove_searches();
    remove_collapsed();
    remove_tags();
    view.tree_size = await api(`/trees/${get_tid()}/size`);
    await set_tree_style();
    reset_node_count();
    store_node_properties();
    reset_zoom();
    reset_position();
    await populate_layouts();
    draw_minimap();
    update();

    const sample_trees = ["ncbi", "GTDB_bact_r95"];  // hardcoded for the moment
    view.allow_modifications = !sample_trees.includes(view.tree);
}


// What happens when the user selects a new shape in the menu.
async function on_shape_change() {
    reset_zoom();
    reset_position();
    draw_minimap();

    update();
}


// Save the available node properties in view.node_properties and the drop-down
// list of the menu that allows to label based on properties.
async function store_node_properties() {
    view.node_properties = await api(`/trees/${get_tid()}/properties`);

    menus.node_properties.children[0].dispose();
    menus.node_properties.addBinding(view, "current_property",
        {index: 0, label: "properties", options: to_opts(view.node_properties)});

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
        else if (param === "shape")
            view.shape = value;
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
}

async function set_consistent_values() {
    if (view.tree === null)
        view.tree = Object.keys(trees)[0];  // select default tree

    view.tree_size = await api(`/trees/${get_tid()}/size`);

    if (view.shape === "circular") {  // adjust zoom nicely so zx == zy
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
        view.nnodes = n.nnodes;
        view.nleaves = n.nleaves;
    });
}


// Set the zoom so the full tree fits comfortably on the screen.
function reset_zoom(reset_zx=true, reset_zy=true) {
    if (!(reset_zx || reset_zy))
        return;

    const size = view.tree_size;

    if (view.shape === "rectangular") {
        if (reset_zx)
            view.zoom.x = 0.6 * div_tree.offsetWidth / size.width;
        if (reset_zy)
            view.zoom.y = 0.9 * div_tree.offsetHeight / size.height;
    }
    else if (view.shape === "circular") {
        const min_w_h = Math.min(div_tree.offsetWidth, div_tree.offsetHeight);
        view.zoom.x = view.zoom.y = min_w_h / (view.rmin + size.width) / 2;
    }
}


function reset_position(reset_x=true, reset_y=true) {
    if (view.shape === "rectangular") {
        if (reset_x)
            view.tl.x = -0.10 * div_tree.offsetWidth / view.zoom.x;
        if (reset_y)
            view.tl.y = -0.05 * div_tree.offsetHeight / view.zoom.y;
    }
    else if (view.shape === "circular") {
        if (reset_x)
            view.tl.x = -div_tree.offsetWidth / view.zoom.x / 2;
        if (reset_y)
            view.tl.y = -div_tree.offsetHeight / view.zoom.y / 2;
    }
}


// Basically rmin, amin, amax (only used for circular representation).
function reset_limits() {
    if (view.shape === "circular") {
        if (!(view.angle.min === -180 && view.angle.max === 180)) {
            view.rmin = 0;
            view.angle.min = -180;
            view.angle.max = 180;
            view.minimap.uptodate = false;
        }
    }
}


// Return an url with the view of the given rectangle of the tree.
function get_url_view(x, y, w, h) {
    const qs = new URLSearchParams({
        x: x, y: y, w: w, h: h,
        tree: view.tree, subtree: view.subtree, shape: view.shape,
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

    if (view.shape === "rectangular") {
        return [x, y];
    }
    else if (view.shape === "circular") {
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

    if (view.shape === "rectangular" && view.smart_zoom)
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


// Return an object opts with opts[txt] = txt for all texts in list.
// This is useful for the input menu lists in tweakpane.
function to_opts(list) {
    const opts = {};
    list.forEach(e => opts[e] = e);
    return opts;
}
