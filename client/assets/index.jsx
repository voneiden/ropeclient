/**
 Ropeclient is a text-based roleplaying platform
 Copyright (C) 2010-2016 Matti Eiden

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

let React = require("react");
let ReactDOM = require("react-dom");
let Ropeclient = require("./Ropeclient");

console.log("Init ropeclient");

ReactDOM.render(<Ropeclient/>, document.getElementById("ropeclient-container"));
