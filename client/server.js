/**
 GrblMgmr is a frontend application to interface with Grbl via GrblMQTT
 Copyright (C) 2016 Matti Eiden

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

let webpack = require("webpack");
let WebpackDevServer = require("webpack-dev-server");
let config = require("./webpack.development.config");


new WebpackDevServer(webpack(config), {
    publicPath: config.output.publicPath,
    hot: true,
    inline: true,
    historyApiFallback: true
}).listen(3000, "0.0.0.0", function (err, result) {
    if (err) {
        console.log(err);
    }

    console.log("Listening at 0.0.0.0:3000");
});