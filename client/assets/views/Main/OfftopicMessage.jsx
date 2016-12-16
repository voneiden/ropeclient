import React from "react";
import classNames from "classnames";
import Message from "./Message";

export default class OfftopicMessage extends Message {
    constructor(props) {
        super(props);
        this.state = {};
    }

    render() {
        console.log(this.props.message);
        let message = this.props.message;

        // System message, no account
        if (!message.a) {
            return (
                <div className="rc-message">
                    {message.v}
                </div>
            );
        }
        else {
            return (
                <div className="rc-message">
                    <span className="rc-timestamp">{message.t}</span>
                    <span className="rc-account">{message.a}</span>
                    <span className="rc-text">{message.v}</span>
                </div>
            );
        }
    }
}


OfftopicMessage.propTypes = {
    message: React.PropTypes.object.isRequired
};