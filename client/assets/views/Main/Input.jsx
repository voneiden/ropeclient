import React from "react";
import ReactDOM from "react-dom";

import classNames from "classnames";
import sha256 from "js-sha256";


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
        if (isTyping != this.state.isTyping) {
            this.setState({
                isTyping: isTyping
            });
            this.props.sendIsTyping(isTyping);
        }
    }

    onKeyPress(event) {
        if (event.key == "Enter" && !event.shiftKey) {
            event.stopPropagation();
            event.preventDefault();
            let message = event.target.value;
            if (this.props.passwordMode) {
                message = sha256(event.target.value + this.props.passwordMode.ss);
                if (this.props.passwordMode.ds) {
                    message = sha256(message + this.props.passwordMode.ds);
                }
            }

            this.props.sendMessage(message);
            event.target.value = "";
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
        if (this.props.passwordMode) {
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