// Functions related to updating (drawing) the view.

import { view, menus, get_tid, on_box_click, on_box_wheel } from "./gui.js";
import { update_minimap_visible_rect } from "./minimap.js";
import { colorize_searches, get_search_class } from "./search.js";
import { on_box_contextmenu } from "./contextmenu.js";
import { colorize_tags } from "./tag.js";
import { colorize_labels } from "./label.js";
import { api } from "./api.js";

export { update, draw_tree, draw, get_class_name };


// Update the view of all elements (gui, tree, minimap).
function update() {
    menus.main.updateDisplay();  // update the info box on the top-right

    draw_tree();

    if (view.minimap.show)
        update_minimap_visible_rect();
}


// Ask the server for a tree in the new defined region, and draw it.
async function draw_tree() {
    const [zx, zy] = [view.zoom.x, view.zoom.y];
    const [x, y] = [view.tl.x, view.tl.y];
    const [w, h] = [div_tree.offsetWidth / zx, div_tree.offsetHeight / zy];

    div_tree.style.cursor = "wait";

    const labels = JSON.stringify(Object.keys(view.labels).map(
        t => [t, view.labels[t].nodetype, view.labels[t].position]));

    const params_rect = {  // parameters we have to pass to the drawer
        "drawer": view.drawer.name, "min_size": view.min_size,
        "zx": zx, "zy": zy, "x": x, "y": y, "w": w, "h": h,
        "collapsed_ids": JSON.stringify(Object.keys(view.collapsed_ids)),
        "labels": labels,
    };

    const params_circ = {  // parameters to the drawer, in circular mode
        ...params_rect,  // all the parameters in params_rect, plus:
        "rmin": view.rmin, "amin": view.angle.min, "amax": view.angle.max,
    };

    const params = view.drawer.type === "rect" ? params_rect : params_circ;
    const qs = new URLSearchParams(params).toString();  // "x=...&y=..."

    try {
        const items = await api(`/trees/${get_tid()}/draw?${qs}`);

        draw(div_tree, items, view.tl, view.zoom);

        view.nnodes = div_tree.getElementsByClassName("node").length;
        colorize_labels();
        colorize_tags();
        colorize_searches();

        if (view.drawer.npanels > 1)
            await draw_aligned(params);

        if (view.drawer.type === "circ") {
            fix_text_orientations();

            if (view.angle.min < -180 || view.angle.max > 180)
                draw_negative_xaxis();
        }
    }
    catch (ex) {
        Swal.fire({
            html: `When drawing: ${ex.message}`,
            icon: "error",
        });
    }

    div_tree.style.cursor = "auto";
}


// Add a line to the svg in div_tree marking the -x axis.
// Useful when we represent circular trees with angles < -180 or > 180.
function draw_negative_xaxis() {
    const x1 = -view.rmin;
    const x2 = x1 - view.tree_size.width;
    const item = ["line", [x1, 0], [x2, 0], "negative_xaxis", []];
    const replace = false;
    draw(div_tree, [item], view.tl, view.zoom, replace);
}


// Append a svg to the given element, with all the items in the list drawn.
// The first child of element will be used or replaced as a svg.
function draw(element, items, tl, zoom, replace=true) {
    const g = create_svg_element("g");

    items.forEach(item => g.appendChild(create_item(item, tl, zoom)));

    put_nodes_in_background(g);

    if (replace)
        replace_svg(element);

    const svg = element.children[0];
    svg.appendChild(g);
}


// Make a copy of the nodeboxes and put them before all the other elements,
// so if they stop being transparent (because they are tagged, or the result
// of a search, or the user changes the node opacity), they do not cover the
// rest of the tree elements.
// The original elements stay transparent in the foreground so the user can
// interact with them (highlighting, opening their contextmenu, etc.).
function put_nodes_in_background(g) {
    const first = g.children[0];  // first svg element, for reference
    Array.from(g.getElementsByClassName("node")).forEach(e => {
        const bg_node = e.cloneNode();
        e.id = "foreground-" + bg_node.id;  // avoid id collisions
        e.classList = ["fg_node"];  // avoid being wrongly selected as a node
        g.insertBefore(bg_node, first);
    });
}


// Replace the svg that is a child of the given element (or just add if none).
function replace_svg(element) {
    const svg = create_svg_element("svg", {
        "width": element.offsetWidth,
        "height": element.offsetHeight,
    });

    if (element.children.length > 0)
        element.children[0].replaceWith(svg);
    else
        element.appendChild(svg);
}


// Draw elements that belong to panels above 0.
async function draw_aligned(params) {
    if (view.drawer.type === "rect") {
        const qs = new URLSearchParams({...params, "panel": 1}).toString();

        const items = await api(`/trees/${get_tid()}/draw?${qs}`);

        draw(div_aligned, items, {x: 0, y: view.tl.y}, view.zoom);
        // NOTE: Only implemented for panel=1 for the moment. We just need to
        //   decide where the graphics would go for panel > 1 (another div? ...)
    }
    else {
        for (let panel = 1; panel < view.drawer.npanels; panel++) {
            const qs = new URLSearchParams({
                ...params, "panel": panel,
                "rmin": view.rmin + panel * view.tree_size.width}).toString();

            const items = await api(`/trees/${get_tid()}/draw?${qs}`);

            const replace = false;
            draw(div_tree, items, view.tl, view.zoom, replace);
        }
    }
}


// Return the graphical (svg) element corresponding to a drawer item.
function create_item(item, tl, zoom) {
    // item looks like ["line", ...] for a line, etc.

    const [zx, zy] = [zoom.x, zoom.y];  // shortcut

    if (item[0] === "nodebox") {
        const [ , box, name, properties, node_id, result_of] = item;

        const b = create_box(box, tl, zx, zy);

        b.id = "node-" + node_id.join("_");  // used in tags

        b.classList.add("node");
        result_of.forEach(t => b.classList.add(get_search_class(t, "results")));

        b.addEventListener("click", event =>
            on_box_click(event, box, node_id));
        b.addEventListener("contextmenu", event =>
            on_box_contextmenu(event, box, name, properties, node_id));
        b.addEventListener("wheel", event =>
            on_box_wheel(event, box), {passive: false});

        if (name.length > 0 || Object.entries(properties).length > 0)
            b.appendChild(create_tooltip(name, properties));

        return b;
    }
    else if (item[0] === "outline") {
        const [ , sbox] = item;

        return create_outline(sbox, tl, zx, zy);
    }
    else if (item[0] === "line") {
        const [ , p1, p2, type, parent_of] = item;

        return create_line(p1, p2, tl, zx, zy, type, parent_of);
    }
    else if (item[0] === "arc") {
        const [ , p1, p2, large, type] = item;

        return create_arc(p1, p2, large, tl, zx, type);
    }
    else if (item[0] === "circle") {
        const [ , center, radius, type] = item;

        return create_circle(center, radius, tl, zx, zy, type);
    }
    else if (item[0] === "text") {
        const [ , box, anchor, text, type] = item;

        return create_text(box, anchor, text, tl, zx, zy, get_class_name(type));
    }
    else if (item[0] === "array") {
        const [ , box, array] = item;
        const [x0, y0, dx0, dy0] = box;
        const dx = dx0 / array.length / zx;

        const [y, dy] = pad(y0, dy0, view.array.padding);

        const g = create_svg_element("g");
        for (let i = 0, x = x0; i < array.length; i++, x+=dx) {
            const r = view.drawer.type === "rect" ?
                create_rect([x, y, dx, dy], tl, zx, zy) :
                create_asec([x, y, dx, dy], tl, zx);
            r.style.stroke = `hsl(${array[i]}, 100%, 50%)`;
            g.appendChild(r);
        }

        return g;
    }
}


// Return a valid class name from a description of a type of element.
function get_class_name(type) {
    return type.replace(/[^A-Za-z0-9_-]/g, '');
}


// Transform the interval [y0, y0+dy0] into one padded with the given fraction.
function pad(y0, dy0, fraction) {
    const dy = dy0 * (1 - fraction);
    return [y0 + (dy0 - dy)/2, dy]
}


function create_svg_element(name, attrs={}) {
    const element = document.createElementNS("http://www.w3.org/2000/svg", name);
    for (const [attr, value] of Object.entries(attrs))
        element.setAttributeNS(null, attr, value);
    return element;
}


// Return a box (rectangle or annular sector).
function create_box(box, tl, zx, zy) {
    const b = view.drawer.type === "rect" ?
                    create_rect(box, tl, zx, zy) :
                    create_asec(box, tl, zx);
    b.classList.add("box");
    return b;
}


function create_rect(box, tl, zx, zy) {
    const [x, y, w, h] = box;

    return create_svg_element("rect", {
        "x": zx * (x - tl.x), "y": zy * (y - tl.y),
        "width": zx * w, "height": zy * h,
    });
}


// Return a svg annular sector, described by box and with zoom z.
function create_asec(box, tl, z) {
    const [r, a, dr, da] = box;
    const large = da > Math.PI ? 1 : 0;
    const p00 = cartesian_shifted(r, a, tl, z),
          p01 = cartesian_shifted(r, a + da, tl, z),
          p10 = cartesian_shifted(r + dr, a, tl, z),
          p11 = cartesian_shifted(r + dr, a + da, tl, z);

    return create_svg_element("path", {
        "d": `M ${p00.x} ${p00.y}
              L ${p10.x} ${p10.y}
              A ${z * (r + dr)} ${z * (r + dr)} 0 ${large} 1 ${p11.x} ${p11.y}
              L ${p01.x} ${p01.y}
              A ${z * r} ${z * r} 0 ${large} 0 ${p00.x} ${p00.y}`,
    });
}

function cartesian_shifted(r, a, tl, z) {
    return {x: z * (r * Math.cos(a) - tl.x),
            y: z * (r * Math.sin(a) - tl.y)};
}


// Return an outline (collapsed version of a box).
function create_outline(sbox, tl, zx, zy) {
    if (view.drawer.type === "rect")
        return create_rect_outline(sbox, tl, zx, zy);
    else
        return create_circ_outline(sbox, tl, zx);
}


// Return a svg horizontal outline.
function create_rect_outline(sbox, tl, zx, zy) {
    const [x, y, dx_min, dx_max, dy] = transform(sbox, tl, zx, zy);

    const dx = view.outline.slanted ? dx_min : dx_max;

    return create_svg_element("path", {
        "class": "outline",
        "d": `M ${x} ${y + dy/2}
              L ${x + dx_max} ${y}
              L ${x + dx} ${y + dy}
              L ${x} ${y + dy/2}`,
    });
}

// Return the sbox translated (from tl) and scaled.
function transform(sbox, tl, zx, zy) {
    const [x, y, dx_min, dx_max, dy] = sbox;
    return [zx * (x - tl.x), zy * (y - tl.y), zx * dx_min, zx * dx_max, zy * dy];
}


// Return a svg outline in the direction of an annular sector.
function create_circ_outline(sbox, tl, z) {
    const [r, a, dr_min, dr_max, da] = sbox;

    const dr = view.outline.slanted ? dr_min : dr_max;

    const large = da > Math.PI ? 1 : 0;
    const p0 = cartesian_shifted(r, a + da/2, tl, z),
          p10 = cartesian_shifted(r + dr_max, a, tl, z),
          p11 = cartesian_shifted(r + dr, a + da, tl, z);

    return create_svg_element("path", {
        "class": "outline",
        "d": `M ${p0.x} ${p0.y}
              L ${p10.x} ${p10.y}
              A ${z * (r + dr_max)} ${z * (r + dr)} 0 ${large} 1 ${p11.x} ${p11.y}
              L ${p0.x} ${p0.y}`,
    });
}


// Return an element that, appended to a svg element (normally a box), will
// make it show a tooltip showing nicely the given name and properties.
function create_tooltip(name, properties) {
    const title = create_svg_element("title", {});
    const text = (name ? name : "(unnamed)") + "\n" +
        Object.entries(properties).map(x => x[0] + ": " + x[1]).join("\n");
    title.appendChild(document.createTextNode(text));
    return title;
}


function create_line(p1, p2, tl, zx, zy, type="", parent_of=[]) {
    const [x1, y1] = [zx * (p1[0] - tl.x), zy * (p1[1] - tl.y)],
          [x2, y2] = [zx * (p2[0] - tl.x), zy * (p2[1] - tl.y)];

    const classes = "line " + type + " " +
        parent_of.map(text => get_search_class(text, "parents")).join(" ");

    return create_svg_element("line", {
        "class": classes,
        "x1": x1, "y1": y1,
        "x2": x2, "y2": y2,
        "stroke": view.line.color,
    });
}


function create_arc(p1, p2, large, tl, z, type="") {
    const [x1, y1] = p1,
          [x2, y2] = p2;
    const r = z * Math.sqrt(x1*x1 + y1*y1);
    const n1 = {x: z * (x1 - tl.x), y: z * (y1 - tl.y)},
          n2 = {x: z * (x2 - tl.x), y: z * (y2 - tl.y)};

    return create_svg_element("path", {
        "class": "line " + type,
        "d": `M ${n1.x} ${n1.y} A ${r} ${r} 0 ${large} 1 ${n2.x} ${n2.y}`,
        "stroke": view.line.color,
    });
}


function create_circle(center, radius, tl, zx, zy, type="") {
    const [x, y] = [zx * (center[0] - tl.x), zy * (center[1] - tl.y)];

    return create_svg_element("circle", {
        "class": "circle " + type,
        "cx": x, "cy": y, "r": view.node.dot.radius,
    });
}


function create_text(box, anchor, text, tl, zx, zy, type="") {
    const [x, y, fs, text_anchor] = view.drawer.type === "rect" ?
        get_text_placement_rect(box, anchor, text, tl, zx, zy, type) :
        get_text_placement_circ(box, anchor, text, tl, zx, type);

    const dx = (type === "name") ? view.name.padding.left * fs / 100 : 0;

    const t = create_svg_element("text", {
        "class": "text " + type,
        "x": x + dx, "y": y,
        "font-size": `${fs}px`,
        "text-anchor": text_anchor,
    });

    t.appendChild(document.createTextNode(text));

    if (view.drawer.type === "circ") {
        const angle = Math.atan2(zy * tl.y + y, zx * tl.x + x) * 180 / Math.PI;
        addRotation(t, angle, x, y);
    }

    return t;
}


// Return position, font size and text anchor to draw text when box is a rect.
function get_text_placement_rect(box, anchor, text, tl, zx, zy, type="") {
    if (text.length === 0)
        throw new Error("please do not try to place empty texts :)")
        // We could, but it's almost surely a bug upstream!

    const [x, y, dx, dy] = box;

    const dx_char = dx / text.length;  // ~ width of 1 char (in tree units)
    const fs_max = Math.min(zx * dx_char * 1.6, zy * dy);
    const fs = font_adjust(fs_max, type);

    const scale = fs / (zy * dy);
    const [ax, ay] = anchor;
    const x_in_tree = x + ax * (1 - scale) * dx,
          y_in_tree = y + ay * (1 - scale) * dy + 0.9 * fs / zy;
    // We give the position as the bottom-left point, the same convention as in
    // svgs. We go a bit up (0.9 instead of 1.0) because of the baseline.

    const dx_in_tree = scale * dx;
    const [x_anchor, text_anchor] = anchored_position(x_in_tree, dx_in_tree, ax);

    return [zx * (x_anchor - tl.x), zy * (y_in_tree - tl.y), fs, text_anchor];
}


// Return position, font size and text anchor to draw text when box is an asec.
function get_text_placement_circ(box, anchor, text, tl, z, type="") {
    if (text.length === 0)
        throw new Error("please do not try to place empty texts :)");
        // We could, but it's almost surely a bug upstream!

    const [r, a, dr, da] = box;
    if (r === 0)
        throw new Error("r cannot be 0 (text would have 0 font size)");

    const dr_char = dr / text.length;  // ~ dr of 1 char (in tree units)
    const fs_max = z * Math.min(dr_char * 1.6, r * da);
    const fs = font_adjust(fs_max, type);

    const scale = fs / (z * r * da);
    const [ar, aa] = anchor;
    const r_in_tree = r + ar * (1 - scale) * dr,
          a_in_tree = a + aa * (1 - scale) * da + 0.8 * (fs / r) / z;
    // We give the position as the bottom-left point, the same convention as in
    // svgs. We go a bit up (0.8 instead of 1.0) because of the baseline.

    const dr_in_tree = scale * dr;
    const [r_anchor, text_anchor] = anchored_position(r_in_tree, dr_in_tree, ar);

    const x_anchor = r_anchor * Math.cos(a_in_tree),
          y_anchor = r_anchor * Math.sin(a_in_tree);

    return [z * (x_anchor - tl.x), z * (y_anchor - tl.y), fs, text_anchor];
}


// Return the x position and the svg text-anchor to place the text for a given
// original in-tree x text position, dx width, and ax anchor.
// This is useful to fine-tune the placement (since dx is just an approximation
// to the exact width of the text).
function anchored_position(x, dx, ax) {
    if (ax < 0.3)
        return [x, "start"];
    else if (ax < 0.6)
        return [x + dx/2, "middle"];
    else
        return [x + dx, "end"];
}


// Flip all the texts in circular representation that look upside-down.
// NOTE: getBBox() is very expensive and requires text to be already in the DOM.
async function fix_text_orientations() {
    const texts = Array.from(div_tree.getElementsByClassName("text"))
        .filter(is_upside_down);

    texts.sort((a, b) => get_font_size(b) - get_font_size(a));

    texts.slice(0, 500).forEach(t => flip_with_bbox(t, t.getBBox()));
    texts.slice(500).forEach(t => flip_with_bbox(t, get_approx_BBox(t)));
}

function is_upside_down(text) {
    const angle = text.transform.baseVal[0].angle;
    return angle < -90 || angle > 90;
}

function get_font_size(text) {
    return Number(text.getAttribute('font-size').slice(0, -2));  // "px"
}


// Apply svg transformation to flip the given text (bounded by bbox).
function flip_with_bbox(text, bbox) {
    addRotation(text, 180, bbox.x + bbox.width/2, bbox.y + bbox.height/2);
}


// Add rotation to element, with angle in degrees and centered around (cx, cy).
function addRotation(element, angle, cx=0, cy=0) {
    const svg = div_tree.children[0];
    const tr = svg.createSVGTransform();
    tr.setRotate(angle, cx, cy);
    element.transform.baseVal.appendItem(tr);
}


// Return an approximate bounding box for the given svg text.
function get_approx_BBox(text) {
    const height = get_font_size(text);
    const x = Number(text.getAttribute("x"));
    const y = Number(text.getAttribute("y")) - height;
    const width = text.childNodes[0].length * height / 1.5;
    return {x, y, width, height};
}


// Return the font size adjusted for the given type of text.
function font_adjust(fs, type) {
    if (type === "name")
        return Math.min(view.name.max_size,
                        (1 - view.name.padding.vertical) * fs);

    for (const expression of Object.keys(view.labels))
        if (type === get_class_name("label_" + expression))
            return Math.min(view.labels[expression].max_size, fs);

    return fs;
}
