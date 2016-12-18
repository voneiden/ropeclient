import React from "react";
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
    message: React.PropTypes.object.isRequired
};