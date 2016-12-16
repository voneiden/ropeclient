import React from "react";
import classNames from "classnames";
import Message from "./Message";

export default class OntopicMessage extends Message {
    constructor(props) {
        super(props);
        this.state = {};
    }

    render() {
        return (
            <div className="rc-message">
                Message
            </div>
        );
    }
}


OntopicMessage.propTypes = {
    message: React.PropTypes.object.isRequired
};