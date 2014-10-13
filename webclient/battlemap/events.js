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
        else if (mode == 1) {
            if (!this.mouse_test) {
                this.mouse_test = [event.offsetX + this.map_view[0], event.offsetY + this.map_view[1]];
            }
            else {
                this.mouse_test = false;
            }
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
        else if (this.mouse_test) {
            request_draw = true;
        }

        // Test hilights
        for (var t=0; t < this.map_tokens.length; t++) {
            var token = this.map_tokens[t];
            var rcx = token.x - this.map_view[0];
            var rcy = token.y - this.map_view[1];
            var radius = token.scale * this.map_scale / 2;
            if (this.test_intersect_point_circle(this.mouse_position, [rcx, rcy, radius])) {
                token.hover = true;
                request_draw = true;
            }
            else {
                if (token.hover) {
                    token.hover = false;
                    request_draw = true;
                }
            }
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