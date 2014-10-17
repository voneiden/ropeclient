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
    this.canvas_scene = document.getElementById('scene');
    this.canvas_mask = document.getElementById('mask');
    this.canvas_light = document.getElementById('light');
    this.root = document.getElementById('body-left');

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
    this.mouse_position_canvas = [0, 0]; // Current mouse position in canvas coordinates
    this.mouse_position_map = [0, 0];    // Current mouse position in map coordinates
    this.mouse_dragging_shadow = false;  // Storing shadow coordinates
    this.mouse_dragging_pan = false; // Storing panning coordinates
    this.mouse_operation = null;  // Current mouse operation (shadow, move, rotate)
    this.mouse_right = false;
    this.mouse_left = false;
    this.mouse_on_token = false; // If mouse is hovering over token, set to token object, otherwise false
    this.mouse_collision = false;
    this.move_collision = false;
    this.mouse_test = false;

    // Map variables
    this.map_background = false; // Background Image()
    this.map_ready = false; // Set true when map background image is loaded, otherwise false
    this.map_view = [0, 0]; // Top left position of the view
    this.map_block_rectangles = []; // Rectangles that block light
    this.map_block_circles = []; // Circles that block light
    this.map_mask = true; // Toggles the mask drawing
    this.map_scale = 50 // Map scale in pixels / meter

    this.map_tokens = []; // Tokens are in format of..
    this.map_selected_token = false; // If a token is selected, set to token, otherwise false
    this.map_waypoints = []; // This displays active waypoint


    // TODO draw battlemap welcome screen?
    this.loadmap();
    this.load_token(280, 250, 1);
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

Battlemap.prototype.load_token = function(x, y, scale, url) {
    if (!url) {
        url = "battlemap/tokens/ka2.jpg"
    }
    var token = {};
    token.image = new Image()
    token.image.src = url;
    token.ready = false;

    token.x = x;
    token.y = y;
    token.scale = scale;

    token.image.onload = function() {
        console.log("Token loaded");
        token.ready = true;
        bm.map_tokens.push(token);
        bm.draw();
    }

    token.image.onerror = function() {
        // TODO: handle token creation failure?
        console.log("Token failed to load");
    }
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
        var w = this.mouse_position_canvas[0] - x;
        var h = this.mouse_position_canvas[1] - y;

        this.mask.fillRect(x, y, w, h);
    }

    for (var t=0; t < this.map_tokens.length; t++) {
        // Render tokens!
        var token = this.map_tokens[t];
        if (!token.ready) { continue; }

        // Render center point
        var rcx = token.x - this.map_view[0];
        var rcy = token.y - this.map_view[1];

        var diameter = token.scale * this.map_scale;
        var radius = diameter/2;

        if (token.selected && this.map_waypoints.length > 0) {
            // Draw existing waypoint lines
            if (this.map_waypoints.length > 1) {
                this.scene.strokeStyle = "rgba(255, 255, 255, 1)";
                this.scene.beginPath();
                for (var w=0; w < this.map_waypoints.length; w++) {
                    var waypoint = this.map_waypoints[w];
                    if (w == 0) {
                        this.scene.moveTo(waypoint[0] - this.map_view[0], waypoint[1] - this.map_view[1]);
                    } else {
                        this.scene.lineTo(waypoint[0] - this.map_view[0], waypoint[1] - this.map_view[1]);
                    }
                }
                this.scene.stroke();
            }

            // Render move line
            var p1 = this.map_waypoints[this.map_waypoints.length - 1];
            var p2 = this.mouse_position_map;

            var radius = token.scale * this.map_scale / 2;

            var d2 = [p2[0] - p1[0], p2[1] - p1[1]];
            var m2 = Math.sqrt(d2[0]*d2[0] + d2[1]*d2[1]);
            var u2 = [d2[0]/m2, d2[1]/m2];
            m2 -= radius;
            d2 = [u2[0]*m2, u2[1]*m2];
            var sp2 = [d2[0] + p1[0], d2[1] + p1[1]];


            this.move_collision = this.test_intersect_move(p1, p2, radius, token);

            if (this.move_collision ) {
                this.scene.strokeStyle = "rgba(255, 0, 0, 1)";
            }
            else {
                this.scene.strokeStyle = "rgba(255, 255, 255, 1)";
            }
            this.scene.beginPath();
            this.scene.moveTo(p1[0] - this.map_view[0], p1[1] - this.map_view[1]);
            this.scene.lineTo(sp2[0] - this.map_view[0], sp2[1] - this.map_view[1]);
            this.scene.stroke();

            this.scene.beginPath();
            this.scene.arc(p2[0] - this.map_view[0], p2[1] - this.map_view[1], radius,0,2*Math.PI)
            this.scene.stroke();

            this.scene.strokeStyle = "rgb(100, 255, 100)";
        }
        else if (token.hover) {
            this.scene.strokeStyle = "rgb(100, 100, 255)";
        }
        else {
            this.scene.strokeStyle = "rgb(0, 0, 0)";
        }

        this.scene.save();
        this.scene.beginPath();
        this.scene.arc(rcx, rcy, radius, 0, 2*Math.PI);
        this.scene.clip();
        this.scene.drawImage(token.image, rcx-radius, rcy-radius, diameter, diameter);
        this.scene.restore();
        this.scene.beginPath();
        this.scene.arc(rcx, rcy, radius, 0, 2*Math.PI);
        this.scene.stroke();
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



/* ================================
 * Battlemap.get_rgba(color, alpha)
 * ================================
 * Convert a list of colors [r, g, b] and alpha value into CSS rgba(r, g, b, a) statement
 */
Battlemap.prototype.get_rgba = function(color, alpha) {
    return "rgba(" + color[0] + ", " + color[1] + ", " + color[2] + ", " + alpha + ")";
}



$(document).ready(function() {
    bm = new Battlemap();
    bm.init();
});