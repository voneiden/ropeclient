import React from "react";
import classNames from "classnames";
import Message from "./Message";
import moment from "moment";

export default class OfftopicMessage extends Message {
    constructor(props) {
        super(props);
        this.state = {};
    }

    render() {

        console.log(this.props.message);
        let message = this.props.message;
        let text = this.replaceDiceRolls(message.v);


        // System message, no account
        if (!message.a) {
            return (
                <div className="rc-message">
                    {message.v}
                </div>
            );
        }
        else {
            let timestamp = moment.unix(message.t).format("HH:mm");
            return (
                <div className="rc-message">
                    <span className="rc-timestamp">[{timestamp}]</span>
                    {" "}
                    <span className="rc-account">&lt;{message.a}&gt;</span>
                    {" "}
                    <span className="rc-text">{text}</span>
                </div>
            );
        }
    }
}


OfftopicMessage.propTypes = {
    message: React.PropTypes.object.isRequired
};