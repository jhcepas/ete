// Minimap-related functions.

import { view, get_tid } from "./gui.js";
import { draw, update } from "./draw.js";
import { api } from "./api.js";

export { draw_minimap, update_minimap_visible_rect, move_minimap_view };


// Draw the full tree on a small div on the bottom-right ("minimap").
async function draw_minimap() {
    if (!view.minimap.show) {
        view.minimap.uptodate = false;
        return;
    }

    adjust_size_and_zoom();

    let qs = `zx=${view.minimap.zoom.x}&zy=${view.minimap.zoom.y}`;
    if (view.drawer.type === "rect")
        qs += "&drawer=Rect";
    else
        qs += `&drawer=Circ&rmin=${view.rmin}` +
              `&amin=${view.angle.min}&amax=${view.angle.max}`;

    const items = await api(`/trees/${get_tid()}/draw?${qs}`);

    const mbw = 3;  // border-width from .minimap css
    const offset = -(div_minimap.offsetWidth - 2*mbw) / view.minimap.zoom.x / 2;
    const tl = view.drawer.type === "rect" ?
        {x: 0, y: 0} :
        {x: offset, y: offset};

    draw(div_minimap, items, tl, view.minimap.zoom);

    remove_nodeboxes();  // we don't want to select or highlight nodes here
    remove_nodedots();  // nor the dots

    view.minimap.uptodate = true;

    update_minimap_visible_rect();
}


function adjust_size_and_zoom() {
    const size = view.tree_size;
    const mbw = 3;  // border-width from .minimap css
    const w = (view.minimap.width / 100) * div_tree.offsetWidth,
          h = (view.minimap.height / 100) * div_tree.offsetHeight;
    if (view.drawer.type === "rect") {
        div_minimap.style.width = `${w}px`;
        div_minimap.style.height = `${h}px`;
        view.minimap.zoom.x = (div_minimap.offsetWidth - 2*mbw) / size.width;
        view.minimap.zoom.y = (div_minimap.offsetHeight - 2*mbw) / size.height;
    }
    else {
        div_minimap.style.width = div_minimap.style.height =
            `${Math.min(w, h)}px`;

        view.minimap.zoom.x = view.minimap.zoom.y =
            (div_minimap.offsetWidth - 2*mbw) / (view.rmin + size.width) / 2;
    }
}


// Remove the boxes that represent the nodes.
function remove_nodeboxes() {
    Array.from(div_minimap.getElementsByClassName("node")).forEach(
        e => e.remove());
    Array.from(div_minimap.getElementsByClassName("fg_node")).forEach(
        e => e.remove());
}


// Remove the dots that represent the nodes.
function remove_nodedots() {
    Array.from(div_minimap.getElementsByClassName("nodedot")).forEach(
        e => e.remove());
}


// Update the minimap's rectangle that represents the current view of the tree.
function update_minimap_visible_rect() {
    const [w_min, h_min] = [5, 5];  // minimum size of the rectangle
    const [round, min, max] = [Math.round, Math.min, Math.max];  // shortcuts

    // Transform all measures into "minimap units" (scaling accordingly).
    const mbw = 3, rbw = 1;  // border-width from .minimap and .visible_rect css
    const mw = div_minimap.offsetWidth - 2 * (mbw + rbw),    // minimap size
          mh = div_minimap.offsetHeight - 2 * (mbw + rbw);
    const wz = view.zoom, mz = view.minimap.zoom;
    const ww = round(mz.x/wz.x * div_tree.offsetWidth),  // viewport size (scaled)
          wh = round(mz.y/wz.y * div_tree.offsetHeight);
    let tx = round(mz.x * view.tl.x),  // top-left corner of visible area
        ty = round(mz.y * view.tl.y);  //   in tree coordinates (scaled)

    if (view.drawer.type === "circ") {
        tx += mw / 2;
        ty += mh / 2;
    }

    const x = max(0, min(tx, mw)),  // clip tx to the interval [0, mw]
          y = max(0, min(ty, mh)),
          w = max(w_min, ww) + min(tx, 0),
          h = max(h_min, wh) + min(ty, 0);

    const rs = div_visible_rect.style;
    rs.left = `${div_minimap.offsetLeft + mbw + x}px`;
    rs.top = `${div_minimap.offsetTop + mbw + y}px`;
    rs.width = `${max(1, min(w, mw - x))}px`;
    rs.height = `${max(1, min(h, mh - y))}px`;
}


// Move the current tree view to the given point in the minimap.
function move_minimap_view(point) {
    const mbw = 3;  // border-width from .minimap css

    // Top-left pixel coordinates of the tree (0, 0) position in the minimap.
    let [x0, y0] = [div_minimap.offsetLeft + mbw, div_minimap.offsetTop + mbw];
    if (view.drawer.type === "circ") {
        x0 += (div_minimap.offsetWidth - 2 * mbw) / 2;
        y0 += (div_minimap.offsetHeight - 2 * mbw) / 2;
    }

    // Size of the visible rectangle.
    const [w, h] = [div_visible_rect.offsetWidth, div_visible_rect.offsetHeight];

    view.tl.x = (point.x - w/2 - x0) / view.minimap.zoom.x;
    view.tl.y = (point.y - h/2 - y0) / view.minimap.zoom.y;
    // So the center of the visible rectangle will be where the mouse is.

    update();
}
