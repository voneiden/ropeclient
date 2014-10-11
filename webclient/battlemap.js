
var background_image;
var debug_start = new Date().getTime(); // Debug fps
var debug_loops = 0
var debug_delta_x = 0;
var debug_delta_y = 0;
var bm_settings_mask = true;
var bm_view = [0, 0];  // Top left coordinates of the current view

function bm_init() {
    console.log("bm_init..");
    var canvas_scene = document.getElementById('battlemap-scene');
    var canvas_mask = document.getElementById('battlemap-mask');
    var root = document.getElementById('root-battlemap');

    canvas_mask.width = canvas_scene.width;
    canvas_mask.height = canvas_scene.height;

    canvas_mask.style.top = canvas_scene.offsetTop;
    canvas_mask.style.left = canvas_scene.offsetLeft;


    load_resources();

    // TODO proper event handler for keyboard input
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
                //draw_battlemap();
                break;

            default:
                console.log(e.which);
                return; // exit this handler for other keys
        }
        //console.warn(debug_delta_x, debug_delta_y)
        draw_battlemap()
        e.preventDefault(); // prevent the default action (scroll / move caret)
    });

    // Mouse events
    canvas_mask.addEventListener('mousedown', function(event) { bm_mouse(1, event) }, false);
    canvas_mask.addEventListener('mouseup', function(event) {bm_mouse(-1, event) }, false);
    canvas_mask.addEventListener('mousemove', function(event) { bm_mouse(0, event) }, false);
    window.addEventListener("resize", function(event) { bm_resize(event) });

    // Disable right click context menu
    canvas_mask.oncontextmenu = function() {
        return false;
    }


}

function load_resources() {
    // Load background
    var src = "battlemap/backgrounds/pic1644363.png"
    background_image = new Image();
    background_image.src = src;
    background_image.onload = function() {
        bm_resize(null);
        draw_battlemap()
    };
}

/* Mouse tracking and commands */
var bm_mouse_shadow_from = false;
var bm_mouse_right_down = false;
var bm_mouse_right_last = null;
var bm_mouse_last = null;
function bm_mouse(type, event) {
    /*
        type
            1: down
            0: move
            -1: up
     */

    // Set this variable to true to redraw the map after event handler finishes
    var request_draw = false;

    // Store mouse movement
    if (type == 0) {
        bm_mouse_last = [event.offsetX, event.offsetY];

        // If currently creating a shadow, update map
        if (bm_mouse_shadow_from) {
            request_draw = true;
        }
    }
    // Handle left click
    if (event.button == 0) {
        // Down event and shift pressed
        if (type == 1 && event.shiftKey) {
            bm_mouse_shadow_from = [event.offsetX + bm_view[0], event.offsetY + bm_view[1]];
            request_draw = true;
        }
        else if (type == -1 && bm_mouse_shadow_from) {
            var x1 = bm_mouse_shadow_from[0];
            var y1 = bm_mouse_shadow_from[1];
            var x2 = event.offsetX + bm_view[0];
            var y2 = event.offsetY + bm_view[1];
            var dx = Math.abs(x2 - x1);
            var dy = Math.abs(y2 - y1);

            if (dx < 5 || dy < 5 || !event.shiftKey) {
                console.log("Rectangle too small!");
            }
            else {
                bm_block_rect.push([[x1, y1],
                                    [x1, y2],
                                    [x2, y2],
                                    [x2, y1]]);
            }

            bm_mouse_shadow_from = false;
            request_draw = true;
        }
    }
    // Right click
    else if (event.button == 2) {
        // Right down
        if (type == 1) {
            bm_mouse_right_down = true;
            bm_mouse_right_last = [event.offsetX, event.offsetY];
        }
        // Right up
        else if (type == -1) {
            bm_mouse_right_down = false;
            bm_mouse_right_last = null;
        }
        // Right motion
        else if (type == 0) {
            var dx = bm_mouse_right_last[0] - event.offsetX;
            var dy = bm_mouse_right_last[1] - event.offsetY;

            bm_view[0] += dx;
            bm_view[1] += dy;

            // Limit view scrolling to background image dimensions
            if (bm_view[0] < 0) { bm_view[0] = 0; }
            if (bm_view[1] < 0) { bm_view[1] = 0; }

            if (background_image.width && background_image.height) {
                var canvas_scene = document.getElementById('battlemap-scene');
                var max_x = background_image.width - canvas_scene.width;
                var max_y = background_image.height - canvas_scene.height;

                if (bm_view[0] > max_x) { bm_view[0] = max_x; }
                if (bm_view[1] > max_y) { bm_view[1] = max_y; }
            }

            bm_mouse_right_last[0] = event.offsetX;
            bm_mouse_right_last[1] = event.offsetY;

            request_draw = true;
        }
    }

    if (request_draw) {
        draw_battlemap();
    }
    event.preventDefault()
    return false;
}

function bm_resize(event) {
    console.log("RES");
    var canvas_scene = document.getElementById('battlemap-scene');
    var canvas_mask = document.getElementById('battlemap-mask');
    var root = $("#root-battlemap");
    //var root = document.getElementById('root-battlemap');
    //var w = root.clientWidth;
    //var h = root.clientHeight;

    var w = root.width();
    var h = root.height();

    if (w > background_image.width) { w = background_image.width }
    if (h > background_image.height) { h = background_image.height }

    // Resize canvas pixel area
    canvas_scene.width = canvas_mask.width = w
    canvas_scene.height = canvas_mask.height = h;

    // Resize canvas CSS
    canvas_scene = $("#battlemap-scene");
    canvas_scene.width(w);
    canvas_scene.height(h);

    canvas_mask = $("#battlemap-mask");
    canvas_mask.width(w);
    canvas_mask.height(h);

    // Redraw
    draw_battlemap();
}

/* Main drawing function */
var bm_block_rect = [[[229, 229],
                      [264, 229],
                      [264, 159],
                      [229, 159]]]

function draw_battlemap() {
    /*
     * Create mask
     * - Ambient color
     * - Render and merge light sources
     * - Line of sight?
     */

    // If line of sight is calculated first
    // the information could possibly be used to determine
    // if a light source is completely invisible (outer diameter fits inside
    // the line of sight shadow?

    var canvas_scene = document.getElementById('battlemap-scene');
    var canvas_mask = document.getElementById('battlemap-mask');
    var canvas_light = document.getElementById('battlemap-light');

    // Get contexts
    var scene = canvas_scene.getContext('2d');
    var mask = canvas_mask.getContext('2d');
    var light = canvas_light.getContext('2d');


    // Draw background_image to scene
    scene.drawImage(background_image, -bm_view[0], -bm_view[1]);


    // Define mask ambient color

    if (bm_settings_mask) {
        console.log("normal fill");
        var ambient_color = [0, 0, 0];
        var ambient_hex = color_to_hex(ambient_color, 1.0);
        mask.fillStyle= ambient_hex;
        mask.fillRect(0, 0, canvas_mask.width, canvas_mask.height);
    }
    else { //TODO: do this only once
        console.log("Clear");
        mask.clearRect(0, 0, canvas_mask.width, canvas_mask.height);
    }


    // Light point sources
    //mask.globalCompositeOperation='lighter';
    //
    var lights = [[300, 300, 200, [0, 200, 0, 1]],
                  [400, 200, 200, [0, 0, 200, 1]],
                  [200, 200, 200, [200, 0, 0, 1]]];
    var lights = [[300+debug_delta_x*5, 250+debug_delta_y*5, 250, [0, 150, 0, 1]],
                  [200, 150, 100,  [150, 0, 0, 1]]];
    //var lights = [[300+debug_delta_x, 250+debug_delta_y, 250, [100, 100, 100, 1]]]


    for (var i=0; i < lights.length; i++) {
        var light_x = lights[i][0]
        var light_y = lights[i][1]
        var light_inner = 0
        var light_outer = lights[i][2]
        var light_color = lights[i][3]

        var light_dx = light_x - light_outer - bm_view[0];
        var light_dy = light_y - light_outer - bm_view[1];
        var light_diameter = light_outer*2;

        canvas_light.width = light_diameter;
        canvas_light.height = light_diameter;

        //console.log(light.width,light.height);
        //console.log("DINGG");

        // TODO: Do shadows and store them
        // Shadow blocks should be either rect or circles
        // Example rect shadow
        var shadow_polygons = generate_shadow_polygons(light_x, light_y, light_outer);

        // Clear light canvas
        light.globalCompositeOperation="source-over"
        light.fillStyle= "rgba(0, 0, 0, 0)";
        light.fillRect(0, 0, canvas_light.width, canvas_light.height);

        // Create mask radial gradient            x            y
        var gradient = light.createRadialGradient(light_outer, light_outer, light_inner, light_outer, light_outer, light_outer);
        /* Gradient is the same!
        gradient.addColorStop(0, "rgba(255, 0, 255, 1.0)");
        gradient.addColorStop(1, "rgba(255, 255, 255, 0.0)");
        */
        gradient.addColorStop(0, color_to_hex(light_color, light_color[3]));
        gradient.addColorStop(1, color_to_hex(light_color, 0));
        light.fillStyle = gradient;
        light.fillRect(0, 0, light_diameter, light_diameter);

        // Apply shadows
        light.globalCompositeOperation = "destination-out"
        light.fillStyle = "rgba(255, 255, 255, 1.0)"
        for (var i_poly=0; i_poly < shadow_polygons.length; i_poly++) {
            var poly = shadow_polygons[i_poly];
            light.beginPath();
            for (var i_point=0; i_point < poly.length; i_point++) {
                var px = poly[i_point][0];
                var py = poly[i_point][1];

                // Convert points relative to light
                px = px - light_x + light_outer
                py = py - light_y + light_outer

                if (i_point == 0) { light.moveTo(px, py); }
                else { light.lineTo(px, py); }
            }
            light.closePath();
            light.fill();
        }

        // Apply to mask
        mask.globalCompositeOperation = "destination-out"
        mask.drawImage(canvas_light, light_dx, light_dy);
        mask.globalCompositeOperation = "source-over"


        scene.globalCompositeOperation="lighter";
        scene.drawImage(canvas_light, light_dx, light_dy);
        scene.globalCompositeOperation="source-over";

        /*
        mask.globalCompositeOperation="lighter";
        mask.drawImage(canvas_light, light_dx, light_dy);
        mask.globalCompositeOperation="source-over";
        */



    }

    if (bm_mouse_shadow_from) {
        mask.fillStyle = "rgba(255, 255, 255, 1)";
        mask.strokeStyle = "rgba(255, 255, 255, 1)";
        var x = bm_mouse_shadow_from[0] - bm_view[0];
        var y = bm_mouse_shadow_from[1] - bm_view[1];
        var w = bm_mouse_last[0] - x;
        var h = bm_mouse_last[1] - y;
        console.log(x, y, w, h);
        mask.fillRect(x, y, w, h);
        //mask.fillRect(bm_mouse_shadow_from[0]-2, bm_mouse_shadow_from[1]-2, 4, 4);

    }

    var debug_end = new Date().getTime();
    $("#details").text(debug_loops / (debug_end - debug_start) * 1000 + "loops per second")
    debug_loops++;

    if (debug_end - debug_start > 2000) {
        debug_loops = 0;
        debug_start = debug_end;
    }
    //window.setTimeout("draw_battlemap()", 1);
}

function generate_shadow_polygons(x, y, max_distance) {

    polygons = []
    // Loop through every rectangle in block list
    for (var i_rect=0; i_rect < bm_block_rect.length; i_rect++) {
        var rect = bm_block_rect[i_rect];

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

        // Add the rect as shadow itself
        /*var relative_rect = [[rect[0][0] - x, rect[0][1] - y],
                             [rect[1][0] - x, rect[1][1] - y],
                             [rect[2][0] - x, rect[2][1] - y],
                             [rect[3][0] - x, rect[3][1] - y]]
        */
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
function color_to_hex(color, alpha) {
    //return "#" + color[0].toString(16) + color[1].toString(16) + color[2].toString(16);
    return "rgba(" + color[0] + ", " + color[1] + ", " + color[2] + ", " + alpha + ")";
}

function bm_absolute_coords_to_view(coords) {
    return [coords[0] - bm_view[0], coords[1] - bm_view[1]];
}
$(document).ready(function(){ bm_init() });