var bm = null; // Global variable to access the battlemap
var debug_start = new Date().getTime(); // Debug fps
var debug_loops = 0
var debug_delta_x = 0;
var debug_delta_y = 0;

/* ===========
 * Battlemap()
 * ===========
 * Our top-level battlemap "class"
 * Once page has loaded, call Battlemap.init()
 */
function Battlemap() {}

/* ================
 * Battlemap.init()
 * ================
 * Initialize the battlemap. Creates canvas variables
 * and event handlers.
 */
Battlemap.prototype.init = function() {
    console.log("BM init called");
    this.canvas_scene = document.getElementById('battlemap-scene');
    this.canvas_mask = document.getElementById('battlemap-mask');
    this.canvas_light = document.getElementById('battlemap-light');
    this.root = document.getElementById('root-battlemap');

    // Define canvas contexts
    this.scene = this.canvas_scene.getContext("2d");
    this.mask = this.canvas_mask.getContext("2d");
    this.light = this.canvas_light.getContext("2d");

    var battlemap = this;

    // Define mouse events
    this.canvas_mask.addEventListener('mousedown', function(event) { battlemap.event_mouse( 1, event) }, false);
    this.canvas_mask.addEventListener('mouseup',   function(event) { battlemap.event_mouse(-1, event) }, false);
    this.canvas_mask.addEventListener('mousemove', function(event) { battlemap.event_mouse( 0, event) }, false);

    // Add resize event
    window.addEventListener("resize", function(event) { battlemap.resize(event) });

    // Disable context menu on right click (we need right click for scrolling)
    this.canvas_mask.oncontextmenu = function() {
        return false;
    }

    // Create variables
    this.mouse_position = [0, 0]; // Current mouse position on canvas
    this.mouse_dragging_shadow = false;  // Storing shadow coordinates
    this.mouse_dragging_pan = false; // Storing panning coordinates
    this.mouse_operation = null;  // Current mouse operation (shadow, move, rotate)
    this.mouse_right = false;
    this.mouse_left = false;

    // Map variables
    this.map_background = false; // Background Image()
    this.map_ready = false; // Set true when map background image is loaded, otherwise false
    this.map_view = [0, 0]; // Top left position of the view
    this.map_block_rectangles = []; // Rectangles that block light
    this.map_block_circles = []; // Circles that block light
    this.map_mask = true; // Toggles the mask drawing

    // TODO draw battlemap welcome screen?
    this.loadmap();
}

/* ======================
 * Battlemap.loadmap(url)
 * ======================
 * Loads a new url as the background image
 */
Battlemap.prototype.loadmap = function(url) {
    if (!url) {
        url = "battlemap/backgrounds/pic1644363.png";
    }
    this.map_background = new Image();
    this.map_background.src = url;
    this.map_ready = false;

    var battlemap = this;
    this.map_background.onload = function() {
        battlemap.map_ready = true;
        battlemap.resize();
        battlemap.draw();
    }

    this.map_background.onerror = function() {
        battlemap.map_background = false;
        battlemap.map_ready = false;
        // TODO: show error message?
    }

}

/* ==================================
 * Battlemap.event_mouse(mode, event)
 * ==================================
 * Handle a mouse event. Mode is 1 for mousedown, 0 for mousemotion and -1 for mouseup.
 */
Battlemap.prototype.event_mouse = function(mode, event) {
    // If request_draw is true, call draw() at the end of the event handler
    var request_draw = false;

    // Left button related things
    if (event.button == 0) {

        // Down event and shift is pressed
        // Set dragging to current position and operation to 'shadow'
        if (mode == 1 && event.shiftKey) {
            this.mouse_dragging_shadow = [event.offsetX + this.map_view[0], event.offsetY + this.map_view[1]];
            request_draw = true;
        }
        // Left mouse released and we're in shadow mode
        else if (mode == -1 && this.mouse_dragging_shadow) {
            var x1 = this.mouse_dragging_shadow[0];
            var y1 = this.mouse_dragging_shadow[1];
            var x2 = event.offsetX + this.map_view[0];
            var y2 = event.offsetY + this.map_view[1];
            var dx = Math.abs(x2 - x1);
            var dy = Math.abs(y2 - y1);

            if (dx < 5 || dy < 5 || !event.shiftKey) {
                console.log("Rectangle too small or shift not pressed.");
            }
            else {
                this.map_block_rectangles.push([[x1, y1],
                                    [x1, y2],
                                    [x2, y2],
                                    [x2, y1]]);
            }

            this.mouse_dragging_shadow = null;
            request_draw = true;
        }
    }

    // Right button related things (scrolling)
    else if (event.button == 2) {
        if (mode == 1) {
            this.mouse_right = true;
            this.mouse_dragging_pan = [event.offsetX, event.offsetY];
        }
        else if (mode == -1) {
            this.mouse_right = false;
            this.mouse_dragging_pan = false;
        }
        else if (mode == 0 && this.mouse_dragging_pan) {
            var dx = this.mouse_dragging_pan[0] - event.offsetX;
            var dy = this.mouse_dragging_pan[1] - event.offsetY;

            this.map_view[0] += dx;
            this.map_view[1] += dy;

            // Limit view scrolling to background image dimensions
            if (this.map_view[0] < 0) { this.map_view[0] = 0; }
            if (this.map_view[1] < 0) { this.map_view[1] = 0; }

            if (this.map_ready && this.map_background.width && this.map_background.height) {
                var max_x = this.map_background.width - this.canvas_scene.width;
                var max_y = this.map_background.height - this.canvas_scene.height;

                if (this.map_view[0] > max_x) { this.map_view[0] = max_x; }
                if (this.map_view[1] > max_y) { this.map_view[1] = max_y; }
            }

            // Update position
            this.mouse_dragging_pan = [event.offsetX, event.offsetY];
            request_draw = true;
        }
    }
    // Store mouse movement
    if (mode == 0) {
        this.mouse_position = [event.offsetX, event.offsetY];

        // Request draw if stuff is being dragged around
        if (this.mouse_dragging_shadow) {
            request_draw = true;
        }
    }

    if (request_draw) {
        this.draw();
    }
    event.preventDefault()
    return false;
}
Battlemap.prototype.event_keyboard = function(event) {
    /*
    $(document).keydown(function(e) {
        switch(e.which) {
            case 37: // left
                debug_delta_x -= 1;
                break;

            case 38: // up
                debug_delta_y -= 1
                break;

            case 39: // right
                debug_delta_x += 1;
                break;

            case 40: // down
                debug_delta_y += 1;
                break;

            case 76:
                bm_settings_mask = !bm_settings_mask;
                console.log("MASK TOGGLE");
                //bm_draw();
                break;

            default:
                console.log(e.which);
                return; // exit this handler for other keys
        }
     */
}


/* =======================
 * Battlemap.resize(event)
 * =======================
 *
 */
Battlemap.prototype.resize = function(event) {
    console.log("RES");
    var root = $("#root-battlemap");

    var w = root.width();
    var h = root.height();

    if (w > this.map_background.width)  { w = this.map_background.width }
    if (h > this.map_background.height) { h = this.map_background.height }

    // Resize canvas pixel area
    this.canvas_scene.width = this.canvas_mask.width = w;
    this.canvas_scene.height = this.canvas_mask.height = h;

    // Resize canvas CSS
    var canvas_scene = $("#battlemap-scene");
    canvas_scene.width(w);
    canvas_scene.height(h);

    var canvas_mask = $("#battlemap-mask");
    canvas_mask.width(w);
    canvas_mask.height(h);

    // Redraw
    this.draw();
}


/* ================
 * Battlemap.draw()
 * ================
 * Draws everything!
 */
Battlemap.prototype.draw = function() {
    // Draw background_image to scene
    this.scene.drawImage(this.map_background, -this.map_view[0], -this.map_view[1]);

    // Define mask ambient color
    if (this.map_mask) {
        var ambient_color = [0, 0, 0];
        this.mask.fillStyle = this.get_rgba(ambient_color, 1.0);;
        this.mask.fillRect(0, 0, this.canvas_mask.width, this.canvas_mask.height);
    }
    else { //TODO: do this only once
        this.mask.clearRect(0, 0, this.canvas_mask.width, this.canvas_mask.height);
    }

    // Light point sources
    var lights = [[300, 300, 200, [0, 200, 0, 1]],
                  [400, 200, 200, [0, 0, 200, 1]],
                  [200, 200, 200, [200, 0, 0, 1]]];
    var lights = [[300+debug_delta_x*5, 250+debug_delta_y*5, 250, [0, 150, 0, 1]],
                  [200, 150, 100,  [150, 0, 0, 1]]];

    for (var i=0; i < lights.length; i++) {
        // Parse the light
        var light_x = lights[i][0]
        var light_y = lights[i][1]
        var light_inner = 0
        var light_outer = lights[i][2]
        var light_color = lights[i][3]

        // Calculate helper variables
        var light_dx = light_x - light_outer - this.map_view[0];
        var light_dy = light_y - light_outer - this.map_view[1];
        var light_diameter = light_outer*2;

        // Scale the canvas to fit the light
        this.canvas_light.width = light_diameter;
        this.canvas_light.height = light_diameter;

        // Generate shadows
        var shadow_polygons = this.create_shadows(light_x, light_y, light_outer);

        // Clear light canvas
        this.light.globalCompositeOperation="source-over"
        this.light.clearRect(0, 0, this.canvas_light.width, this.canvas_light.height);

        // Create mask radial gradient            x            y
        var gradient = this.light.createRadialGradient(light_outer, light_outer, light_inner, light_outer, light_outer, light_outer);
        gradient.addColorStop(0, this.get_rgba(light_color, light_color[3]));
        gradient.addColorStop(1, this.get_rgba(light_color, 0));
        this.light.fillStyle = gradient;
        this.light.fillRect(0, 0, light_diameter, light_diameter);

        // Apply shadows
        this.light.globalCompositeOperation = "destination-out"
        this.light.fillStyle = "rgba(255, 255, 255, 1.0)"
        for (var i_poly=0; i_poly < shadow_polygons.length; i_poly++) {
            var poly = shadow_polygons[i_poly];
            this.light.beginPath();
            for (var i_point=0; i_point < poly.length; i_point++) {
                var px = poly[i_point][0];
                var py = poly[i_point][1];

                // Convert points relative to light
                px = px - light_x + light_outer
                py = py - light_y + light_outer

                if (i_point == 0) { this.light.moveTo(px, py); }
                else { this.light.lineTo(px, py); }
            }
            this.light.closePath();
            this.light.fill();
        }

        // Apply results to shadow mask
        this.mask.globalCompositeOperation = "destination-out"
        this.mask.drawImage(this.canvas_light, light_dx, light_dy);
        this.mask.globalCompositeOperation = "source-over"

        // Apply results to scene (colorize)
        this.scene.globalCompositeOperation="lighter";
        this.scene.drawImage(this.canvas_light, light_dx, light_dy);
        this.scene.globalCompositeOperation="source-over";
    }

    // If creating a new shadow, draw the shadow box
    if (this.mouse_dragging_shadow) {
        this.mask.fillStyle = "rgba(255, 255, 255, 1)";
        this.mask.strokeStyle = "rgba(255, 255, 255, 1)";
        var x = this.mouse_dragging_shadow[0] - this.map_view[0];
        var y = this.mouse_dragging_shadow[1] - this.map_view[1];
        var w = this.mouse_position[0] - x;
        var h = this.mouse_position[1] - y;

        this.mask.fillRect(x, y, w, h);
    }

    var debug_end = new Date().getTime();
    $("#details").text(debug_loops / (debug_end - debug_start) * 1000 + "loops per second")
    debug_loops++;

    if (debug_end - debug_start > 2000) {
        debug_loops = 0;
        debug_start = debug_end;
    }
    //window.setTimeout("bm_draw()", 1);
}

/* ============================================
 * Battlemap.create_shadows(x, y, max_distance)
 * ============================================
 * This function takes a point source (x,y) as an input
 * and generates relevant shadows within the distance of max_distance.
 * * Can be used to create light shadows and also line of sight shadows.
 */
Battlemap.prototype.create_shadows = function(x, y, max_distance) {
    var polygons = []

    // Loop through every rectangle in block list
    for (var i_rect=0; i_rect < this.map_block_rectangles.length; i_rect++) {
        var rect = this.map_block_rectangles[i_rect];

        // Check distance
        var in_range = false;
        var angle_dict = {};
        var angle_list = [];

        for (var i_point=0; i_point < rect.length; i_point++) {
            var point = rect[i_point];
            var rx = point[0] - x;
            var ry = point[1] - y;
            var distance = Math.sqrt(rx*rx + ry*ry);
            if (!in_range && distance < max_distance) {
                in_range = true;
                //console.log("Block rect", i_rect, "is in range for light at",x,y,"with distance of", distance, "/", max_distance);
            }

            var ux = rx / distance;
            var uy = ry / distance;
            var angle = Math.atan2(ux, uy) + Math.PI;
            angle_dict[angle] = [rx, ry, ux, uy]; // TODO make sure duplicates are not allowed
            angle_list.push(angle);
        }

        if (!in_range) {
            //console.log("Block rect ", i_rect, " is not in range for light at ",x, " ", y);
            continue;
        }

        // Push the shadow rectangle object itself in the shadow list
        polygons.push(rect);

        // Next step is to sort the angles and do the step analysis
        angle_list.sort();
        //console.log("Ang",angle_list);
        var step_dict = {};
        var step_list = [];
        var n_step;
        var i_angle;
        var n_angle;
        var step;

        for (var i_step=0; i_step < 4; i_step++) {
            if (i_step == 3) { n_step = 0; }
            else { n_step = i_step + 1; }

            i_angle = angle_list[i_step];
            n_angle = angle_list[n_step];

            //console.log(i_angle, n_angle);

            step = Math.abs(n_angle - i_angle);
            if (step >= Math.PI) {
                step = Math.abs(step - Math.PI*2)
            }

            step_list.push(step)
            step_dict[step] = [i_angle, n_angle]; // TODO make sure duplicates are not allowed
        }

        // Sort the steps and grab the biggest step
        step_list.sort();

        //console.log(step_list);
        //console.log(step_dict[step_list[3]]);

        var shadow_angles = step_dict[step_list[3]];
        var shadow_polygon = [];

        //console.log("Start",  angle_dict[shadow_angles[0]])
        //console.log("End",  angle_dict[shadow_angles[1]])
        // Add first selected angle point
        var start = angle_dict[shadow_angles[0]];
        var start_x = start[0] + x; // Convert relative position to absolute position;
        var start_y = start[1] + y;


        var end = angle_dict[shadow_angles[1]];
        var end_x = end[0] + x;
        var end_y = end[1] + y;

        // Push the start
        shadow_polygon.push([start_x, start_y])

        // Push projection point 1
        var proj1_x = start[2] * 1000 + x;
        var proj1_y = start[3] * 1000 + y;
        //console.log(proj1_x, proj1_y,start[2], start[3]);
        shadow_polygon.push([proj1_x, proj1_y]);

         // Push projection point 2
        var proj2_x = end[2] * 1000 + x;
        var proj2_y = end[3] * 1000 + y;
        shadow_polygon.push([proj2_x, proj2_y]);

        // Push the end
        shadow_polygon.push([end_x, end_y])

        polygons.push(shadow_polygon);
    }
    return polygons;
}

/* ================================
 * Battlemap.get_rgba(color, alpha)
 * ================================
 * Convert a list of colors [r, g, b] and alpha value into CSS rgba(r, g, b, a) statement
 */
Battlemap.prototype.get_rgba = function(color, alpha) {
    return "rgba(" + color[0] + ", " + color[1] + ", " + color[2] + ", " + alpha + ")";
}

/* ========================================
 * Battlemap.test_intersect_CCW(p1, p2, p3)
 * ========================================
 * Helper function for Battlemap.test_intersect_line_line()
 * Source: http://stackoverflow.com/a/16725715/1744706
 */
Battlemap.prototype.test_intersect_CCW = function(p1, p2, p3) {
  return (p3[1] - p1[1]) * (p2[0] - p1[0]) > (p2[1] - p1[1]) * (p3[0] - p1[0]);
}

/* ==================================================
 * Battlemap.test_intersect_line_line(p1, p2, p3 ,p4)
 * ==================================================
 * Test if line segment [p1, p2] intersects with line
 * segment [p3, p4].
 */
Battlemap.prototype.test_intersect_line_line = function(p1, p2, p3, p4) {
  return (this.test_intersect_CCW(p1, p3, p4) != this.test_intersect_CCW(p2, p3, p4)) && (this.test_intersect_CCW(p1, p2, p3) != this.test_intersect_CCW(p1, p2, p4));
}

/* ===================================================
 * Battlemap.test_intersect_point_poly(point, polygon)
 * ===================================================
 * Test if point is inside polygon
 * Source: http://stackoverflow.com/a/2922778/1744706
 */
Battlemap.prototype.test_intersect_point_poly = function(point, polygon) {
    var c = false;
    for (var i= 0,j=polygon.length-1; i < polygon.length; j=i++) {
        if (((polygon[i][1] > point[1]) != (polygon[j][1] > point[1])) &&
            (point[0] < (polygon[j][0] - polygon[i][0]) *
                        (point[1] - polygon[i][1]) / (polygon[j][1] - polygon[i][1]) + polygon[i][0])) {
            c = !c;
       }
    }
    return c;
}

/*
 * Battlemap.test_intersect_point_circle(point, circle)
 * ====================================================
 * Test if point (x,y) is inside circle (x, y, radius)
 */
Battlemap.prototype.test_intersect_point_circle = function(point, circle) {
    return Math.sqrt(Math.pow(point[0]-circle[0], 2) + Math.pow(point[1]-circle[1], 2 )) < circle[3];
}

/*
 * Battlemap.test_intersect_line_circle(p1, p2, circle)
 * ====================================================
 * Test if line segment p1,p2 is intersects circle
 * Source: http://stackoverflow.com/a/1084899/1744706
 */
Battlemap.prototype.test_intersect_line_circle = function(p1, p2, circle) {

    var sx = p2[0] - p1[0];
    var sy = p2[1] - p1[1];

    var cx = p1[0] - circle[0];
    var cy = p1[1] - circle[1];

    var a = sx*sx + sy*sy;
    var b = 2 * (cx * sx + cy * sy);
    var c = cx*cx + cy*cy - circle[2] * circle[2];

    var discriminant = b*b - 4*a*c;
    if (discriminant < 0) { return false; }
    else { return true; }
}

$(document).ready(function() {
    bm = new Battlemap();
    bm.init();
});