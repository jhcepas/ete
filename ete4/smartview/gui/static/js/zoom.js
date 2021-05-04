// Zoom-related functions.

import { view } from "./gui.js";
import { update } from "./draw.js";
import { draw_minimap, update_minimap_visible_rect } from "./minimap.js";

export { zoom_around, zoom_into_box, zoom_towards_box };


const zooming = {qz: {x: 1, y: 1}, timeout: undefined};


// Zoom the current view into the area defined by the given box, with a border
// marking the fraction of zoom-out (to see a bit the surroundings).
function zoom_into_box(box, border=0.10) {
    if (view.drawer.type === "rect") {
        const [x, y, w, h] = box;
        view.tl.x = x - border * w;
        view.tl.y = y - border * h;
        view.zoom.x = div_tree.offsetWidth / (w * (1 + 2 * border));
        view.zoom.y = div_tree.offsetHeight / (h * (1 + 2 * border));
    }
    else if (view.drawer.type === "circ") {
        const [r, a, dr, da] = box;
        const points = [[r, a], [r, a+da], [r+dr, a], [r+dr, a+da]];
        const xs = points.map(([r, a]) => r * Math.cos(a)),
              ys = points.map(([r, a]) => r * Math.sin(a));
        const [x, y] = [Math.min(...xs), Math.min(...ys)];
        const [w, h] = [Math.max(...xs) - x, Math.max(...ys) - y];
        const [zx, zy] = [div_tree.offsetWidth / w, div_tree.offsetHeight / h];
        if (zx < zy) {
            view.tl.x = x - border * w;
            view.zoom.x = view.zoom.y = zx / (1 + 2 * border);
            view.tl.y = y - (div_tree.offsetHeight / zx - h) / 2 - border * h;
        }
        else {
            view.tl.y = y - border * h;
            view.zoom.x = view.zoom.y = zy / (1 + 2 * border);
            view.tl.x = x - (div_tree.offsetWidth / zy - w) / 2 - border * w;
        }
    }
    update();
}

window.zoom_into_box = zoom_into_box;  // exposed so it can be called in onclick


// Zoom maintaining the given point on the screen.
function zoom_around(point, zoom_in, do_zoom={x:true, y:true}, qz=undefined) {
    if (!qz)
        qz = {x: (zoom_in ? 1.25 : 0.8),  // zoom change (quotient)
              y: (zoom_in ? 1.25 : 0.8)};

    if (view.drawer.type === "rect") {
        zoom_xy(point, qz, do_zoom);
    }
    else if (view.drawer.type === "circ") {
        if (do_zoom.x) {
            do_zoom.y = true;  // both dimensions zoom together in circular
            zoom_xy(point, qz, do_zoom);
        }
        else if (do_zoom.y) {
            zoom_angular(point, qz);
        }
    }
}


// Zoom around given point changing the x and y zoom by a factor qz.x and qz.y.
function zoom_xy(point, qz, do_zoom) {
    if (do_zoom.x) {
        const zoom_new = qz.x * view.zoom.x;
        view.tl.x += (1 / view.zoom.x - 1 / zoom_new) * point.x;
        view.zoom.x = zoom_new;
        zooming.qz.x *= qz.x;
    }

    if (do_zoom.y) {
        const zoom_new = qz.y * view.zoom.y;
        view.tl.y += (1 / view.zoom.y - 1 / zoom_new) * point.y;
        view.zoom.y = zoom_new;
        zooming.qz.y *= qz.y;
    }

    if (do_zoom.x || do_zoom.y)
        smooth_zoom(point);
}


// Zoom (around given point and by a factor qz.y) by changing the angular limits.
function zoom_angular(point, qz) {
    const x = view.tl.x + point.x / view.zoom.x,
          y = view.tl.y + point.y / view.zoom.y;
    const angle = Math.atan2(y, x) * 180 / Math.PI;

    view.angle.min = angle + qz.y * (view.angle.min - angle);
    view.angle.max = angle + qz.y * (view.angle.max - angle);

    if (zooming.timeout)
        window.clearTimeout(zooming.timeout);

    zooming.timeout = window.setTimeout(() => {
        zooming.timeout = undefined;
        draw_minimap();
        update();
    }, 50);  // 50 ms until we actually update (if not cancelled before!)
}


// Zoom adaptatively so that the given box tends to occupy the full screen.
function zoom_towards_box(box, point, zoom_in, do_zoom) {
    let qx, qy;
    if (zoom_in) {
        const [dx, dy] = [box[2], box[3]];
        qx = 0.8 * div_tree.offsetWidth / (dx * view.zoom.x) - 1;
        qy = 0.8 * div_tree.offsetHeight / (dy * view.zoom.y) - 1;
    }
    else {
        const [dx, dy] = [3 * view.tree_size.width, 3 * view.tree_size.height];
        qx = div_tree.offsetWidth / (dx * view.zoom.x) - 1,
        qy = div_tree.offsetHeight / (dy * view.zoom.y) - 1;
    }
    const qz = {x: 1 + 0.2 * Math.atan(qx),
                y: 1 + 0.2 * Math.atan(qy)};

    zoom_xy(point, qz, do_zoom);
}


// Zoom by scaling the svg, and really update it only after a timeout.
function smooth_zoom(point) {
    if (zooming.timeout)
        window.clearTimeout(zooming.timeout);

    Array.from(div_tree.children[0].children).forEach(g =>
        g.setAttribute("transform",
            `scale(${zooming.qz.x}, ${zooming.qz.y}) ` +
            `translate(${(1 / zooming.qz.x - 1) * point.x}
                    ${(1 / zooming.qz.y - 1) * point.y})`));

    if (view.minimap.show)
        update_minimap_visible_rect();

    zooming.timeout = window.setTimeout(() => {
        zooming.qz.x = zooming.qz.y = 1;
        zooming.timeout = undefined;
        update();
    }, 50);  // 50 ms until we actually update (if not cancelled before!)
}
