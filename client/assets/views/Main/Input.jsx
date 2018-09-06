import React from "react";
import ReactDOM from "react-dom";
import {inject, observer} from "mobx-react";
import classNames from "classnames";
import sha256 from "js-sha256";
import Net from "../../utils/net";


@inject("stateStore")
@observer
export default class Input extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            isTyping: false
        };

        this._inputElement = null;
        this._focusPreUpdate = null;

        this.onChange = this.onChange.bind(this);
        this.onKeyPress = this.onKeyPress.bind(this);

    }

    onChange(event) {
        console.log("OOOH", event.target);

        let isTyping = event.target.value.length > 0;
        console.log(event.target.value.length > 0);
        if (isTyping !== this.props.stateStore.isTyping) {
            this.props.stateStore.isTyping = isTyping;
        }
    }

    onKeyPress(event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.stopPropagation();
            event.preventDefault();
            let message = event.target.value;
            if (this.props.stateStore.isPasswordMode) {
                message = sha256(event.target.value + this.props.stateStore.passwordMode.ss);
                if (this.props.stateStore.passwordMode.ds) {
                    message = sha256(message + this.props.stateStore.passwordMode.ds);
                }
            }

            Net.sendText(message);
            event.target.value = "";
            if (this.props.stateStore.isTyping) {
                this.props.stateStore.isTyping = false;
            }
        }
    }

    focus() {

    }

    componentDidMount() {
        if (this._inputElement) {
            this._inputElement.focus();
        }
    }

    componentWillUpdate() {
        this._focusPreUpdate = document.activeElement == this._inputElement;
    }
    componentDidUpdate() {
        if (this._focusPreUpdate && this._inputElement) {
            this._inputElement.focus();
        }
    }

    render() {
        if (this.props.stateStore.isPasswordMode) {
            return (
                <div id ="rc-input" className="flex flex-row">
                    <input
                        type="password"
                        className="flex-grow"
                        onChange={this.onChange}
                        onKeyPress={this.onKeyPress}
                        ref={ (input) => { this._inputElement = input; }}
                    />
                </div>
            );
        }
        else {
            return (
                <div id ="rc-input" className="flex flex-row">
                    <textarea
                        className="flex-grow"
                        onChange={this.onChange}
                        onKeyPress={this.onKeyPress}
                        ref={ (input) => { this._inputElement = input; }}
                    />
                </div>
            );
        }
    }
}