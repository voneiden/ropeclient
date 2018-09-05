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
import {inject} from "mobx-react";
import "./styles/main.scss";
import classNames from "classnames";
import MainView from "./views/MainView";
import ConfigView from "./views/ConfigView";

@inject("stateStore")
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
            mainContent = <ConfigView/>;
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