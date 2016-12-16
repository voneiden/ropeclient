import React from "react";
import classNames from "classnames";


export default class Message extends React.Component {
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


Message.propTypes = {

};