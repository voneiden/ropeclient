import React from "react";
import PropTypes from "prop-types";

import classNames from "classnames";
import OfftopicMessage from "./OfftopicMessage";


export default class OfftopicContainer extends React.Component {
    constructor(props) {
        super(props);

        this.state = {};

    }

    render() {
        let messages = this.props.messages.map(function (message, index) {
            return <OfftopicMessage message={message} key={index}/>;
        });
        return (
            <div id ="rc-offtopic" className="flex-grow">
                { messages }
            </div>
        );
    }
}


OfftopicContainer.propTypes = {
    messages: PropTypes.array.isRequired
};