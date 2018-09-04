import React from "react";
import PropTypes from "prop-types";

import classNames from "classnames";
import Message from "./Message";

export default class OntopicMessage extends Message {
    constructor(props) {
        super(props);
        this.state = {};
    }

    render() {
        console.log("Render ont message", this.props.message);
        return (
            <div className="rc-message">
                {this.props.message.v}
            </div>
        );
    }
}


OntopicMessage.propTypes = {
    message: PropTypes.object.isRequired
};