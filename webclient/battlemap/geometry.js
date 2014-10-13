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

/* ====================================================
 * Battlemap.test_intersect_point_circle(point, circle)
 * ====================================================
 * Test if point (x,y) is inside circle (x, y, radius)
 */
Battlemap.prototype.test_intersect_point_circle = function(point, circle) {
    return Math.sqrt(Math.pow(point[0]-circle[0], 2) + Math.pow(point[1]-circle[1], 2 )) < circle[2];
}

/* ====================================================
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

    var d = b*b - 4*a*c;
    if (d < 0) { return false; }
    else {
        // Ray has hit the circle. Now check segments
        d = Math.sqrt(d);

        var t1 = (-b - d)/(2*a);
        var t2 = (-b + d)/(2*a);

        if ( t1 >= 0 && t1 <= 1 ) { return true; }
        else if ( t2 >= 0 && t2 <= 1 ) { return true; }
        else { return false; }
    }
}

/* ========================================================
 * Battlemap.test_intersect_circle_circle(circle1, circle2)
 * ========================================================
 * Test if two circles intersect
 */
Battlemap.prototype.test_intersect_circle_circle = function(circle1, circle2) {
    var dx = circle1[0] - circle2[0];
    var dy = circle1[1] - circle2[1];

    return Math.sqrt(dx*dx + dy*dy) < circle1[2] + circle2[2];
}

/*
 * Battlemap.test_intersect_move(p1, p2, radius, ignore_token)
 * ===========================================================
 * Return true if a line with a width of radius drawn from p1 to p2
 * or a circle of radius at p2 intersects with any blocks in the
 * active map. Define optional ignore_token to ignore the 'starting'
 * token. Points are in absolute coordinatres
 */
Battlemap.prototype.test_intersect_move = function(p1, p2, radius, ignore_token) {
    var dp = [p2[0] - p1[0], p2[1] - p1[1]]; // Shift to origin
    var mp = Math.sqrt(dp[0]*dp[0] + dp[1] * dp[1]); // Magnitude
    var up = [dp[0] / mp, dp[1] / mp]; // Unit vector

    var rup = [-up[1], up[0]]; // Unit vector to right
    var lup = [up[1], -up[0]]; // Unit vector to left

    var rp = [rup[0] * radius, rup[1] * radius];
    var lp = [lup[0] * radius, lup[1] * radius];

    var p1r = [p1[0] + rp[0], p1[1] + rp[1]];
    var p2r = [p2[0] + rp[0], p2[1] + rp[1]];

    var p1l = [p1[0] + lp[0], p1[1] + lp[1]];
    var p2l = [p2[0] + lp[0], p2[1] + lp[1]];

    var p2circle = [p2[0], p2[1], radius]

    var collision = false;

    for (var z=0; z < this.map_block_rectangles.length; z++) {
        var rect = this.map_block_rectangles[z];
        for (var n = 0, m = rect.length- 1; n < rect.length; m = n++) {
            var p3 = rect[n];
            var p4 = rect[m];
            if (this.test_intersect_line_line(p1r, p2r, p3, p4) ||
                this.test_intersect_line_line(p1l, p2l, p3, p4) ||
                this.test_intersect_point_poly(p3, [p1r, p2r, p2l, p1l]) ||
                this.test_intersect_line_circle(p3, p4, p2circle)) {
                collision = true;
                break;
            }
        }
    }
    for (var t=0; t < this.map_tokens.length; t++) {
        var token = this.map_tokens[t];
        if (token == ignore_token) { continue; }

        var token_circle = [token.x, token.y, token.scale * this.map_scale / 2]
        if (this.test_intersect_circle_circle(token_circle, p2circle) ||
            this.test_intersect_line_circle(p1r, p2r, token_circle) ||
            this.test_intersect_line_circle(p1l, p2l, token_circle)) {
            collision = true;
            break;
        }
    }
    return collision;
}

Battlemap.prototype.find_point_token = function(point) {
    for (var t=0; t < this.map_tokens.length; t++) {
        var token = this.map_tokens[t];
        if (this.test_intersect_point_circle(point, [token.x, token.y, token.scale * this.map_scale / 2])) {
            return token;
        }
    }
    return false;
}