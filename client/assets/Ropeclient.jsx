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

import React from "react";
import "./styles/main.scss";
import classNames from "classnames";
import MainView from "./views/MainView";

export default class Ropeclient extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            ontopicMessages: [],
            offtopicMessages: []
        };
        this.socket = null;

        this.connect = this.connect.bind(this);
        this.onSocketOpen = this.onSocketOpen.bind(this);
        this.onSocketClose = this.onSocketClose.bind(this);
        this.onSocketMessage = this.onSocketMessage.bind(this);
        this.onSocketError = this.onSocketError.bind(this);

        this.process = this.process.bind(this);

    }
    /*
     * Connection specific methods
     */
    connect(url) {
        this.socket = new WebSocket("ws://localhost:8090");

    }

    onSocketOpen() {

    }
    onSocketClose() {

    }
    onSocketError() {

    }
    onSocketMessage(event) {
        try {
            return this.process(JSON.parse(event.data));
        }
        catch (ex) {
            console.warn("Failed to parse data: " + event.data, ex);
            return false;
        }


    }

    process(data) {
        if (!data.k) {
            console.warn("Invalid data, no key", data);
            return false;
        }

        switch (data.k) {
            case "oft":
                this.setState({
                    offtopicMessages: this.state.offtopicMessages.concat(data)
                });
                break;
            case "ont":
                this.setState({
                    ontopicMessages: this.state.ontopicMessages.concat(data)
                });
                break;

            case "pwd":
                break;
            case "clr":
                switch (data.v) {
                    case "oft":
                        this.setState({
                            offtopicMessages: []
                        });
                        break;
                    case "ont":
                        this.setState({
                            ontopicMessages: []
                        });
                        break;
                    default:
                        this.setState({
                            offtopicMessages: [],
                            ontopicMessages: []
                        });
                        break;
                }
                break;
            default:
                console.warn("Unknown data packet", data);
        }
    }

    render() {
        console.log();
        return (
            <div id ="ropeclient-app">
                <MainView
                    ontopicMessages={this.state.ontopicMessages}
                    offtopicMessages={this.state.offtopicMessages}
                />
            </div>
        );
    }
}