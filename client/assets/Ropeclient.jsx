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
import ConfigView from "./views/ConfigView";

export default class Ropeclient extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            showConfig: false,
            ontopicMessages: [],
            offtopicMessages: [],
            passwordMode: false,
            players: {}
        };
        this.socket = null;

        this.connect = this.connect.bind(this);
        this.send = this.send.bind(this);
        this.sendIsTyping = this.sendIsTyping.bind(this);
        this.onSocketOpen = this.onSocketOpen.bind(this);
        this.onSocketClose = this.onSocketClose.bind(this);
        this.onSocketMessage = this.onSocketMessage.bind(this);
        this.onSocketError = this.onSocketError.bind(this);

        this.toggleConfig = this.toggleConfig.bind(this);

        this.process = this.process.bind(this);

    }

    componentDidMount() {
        this.connect();
    }

    /*
     * Connection specific methods
     */
    connect(url) {
        this.socket = new WebSocket("ws://localhost:8090");
        this.socket.onopen = this.onSocketOpen;
        this.socket.onerror = this.onSocketError;
        this.socket.onmessage = this.onSocketMessage;
        this.socket.onclose = this.onSocketClose;

    }

    send(text) {
        if (this.socket) {
            let message = {
                k: "msg",
                v: text ? text : ""
            };
            console.log("Send", message);
            this.socket.send(JSON.stringify(message));
        }
        if (this.state.passwordMode) {
            this.setState({
                passwordMode: false
            });
        }
    }
    sendIsTyping(isTyping) {
        if (this.socket) {
            let message = {
                k: isTyping ? "pit" : "pnt",
            };
            console.log("Send", message);
            this.socket.send(JSON.stringify(message));
        }
    }

    onSocketOpen() {
        this.send("test");
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
            console.error("Failed to parse data: " + event.data, ex);
            return false;
        }


    }

    process(dataset) {

        if (!Array.isArray(dataset)) {
            dataset = [dataset];
        }
        let clearOfftopic = false;
        let offtopicMessages = [];

        let clearOntopic = false;
        let ontopicMessages = [];

        let state = {
            passwordMode: false
        };

        for (let data of dataset) {
            if (!data.k) {
                console.warn("Invalid data, no key", data);
                return false;
            }

            switch (data.k) {
                case "oft":
                    offtopicMessages.push(data);
                    break;
                case "ont":
                    console.log("Got ont message");
                    ontopicMessages.push(data);
                    break;

                case "pwd":
                    console.log("Password mode requested:", data);
                    state.passwordMode = data;

                    break;
                case "clr":
                    switch (data.v) {
                        case "oft":
                            clearOfftopic = true;
                            offtopicMessages = [];
                            break;
                        case "ont":
                            clearOntopic = true;
                            ontopicMessages = [];
                            break;
                        default:
                            clearOfftopic = clearOntopic = true;
                            offtopicMessages = [];
                            offtopicMessages = [];
                            break;
                    }
                    break;

                case "pll": {
                    let players = {};
                    for (let player of data.v) {
                        players[player] = false;
                    }
                    state.players = players;
                    break;
                }

                case "pit": {
                    let update = {};
                    update[data.a] = true;
                    state.players = Object.assign(this.state.players, update);
                    console.log("pit", state.players);
                    break;
                }

                case "pnt": {
                    let update = {};
                    update[data.a] = false;
                    state.players = Object.assign(this.state.players, update);
                    console.log("pnt", state.players);
                    break;
                }

                default:
                    console.warn("Unknown data packet", data);
            }
        }

        if (offtopicMessages.length || clearOfftopic) {
            state.offtopicMessages = clearOfftopic ? offtopicMessages : this.state.offtopicMessages.concat(offtopicMessages);
        }

        if (ontopicMessages.length || clearOntopic) {
            state.ontopicMessages = clearOntopic ? ontopicMessages : this.state.ontopicMessages.concat(ontopicMessages);
        }

        this.setState(state);
    }

    toggleConfig() {
        this.setState({
            showConfig: !this.state.showConfig
        });
    }

    render() {
        console.log();
        let mainContent;
        if (this.state.showConfig) {
            mainContent = <ConfigView></ConfigView>;
        } else {
            mainContent = <MainView
                    ontopicMessages={this.state.ontopicMessages}
                    offtopicMessages={this.state.offtopicMessages}
                    passwordMode={this.state.passwordMode}
                    players={this.state.players}
                    sendMessage={this.send}
                    sendIsTyping={this.sendIsTyping}

                />;
        }
        return (
            <div id ="ropeclient-app" className="flex-column">
                <div id="rc-configure-btn" onClick={ this.toggleConfig }><i className="material-icons">settings</i></div>
                { mainContent }
            </div>
        );
    }
}