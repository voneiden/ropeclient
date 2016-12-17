import React from "react";
import classNames from "classnames";
import OntopicMessage from "./OntopicMessage";


export default class OntopicContainer extends React.Component {
    constructor(props) {
        super(props);

        this.state = {};

    }

    render() {
        let messages = this.props.messages.map(function (message, index) {
            return <OntopicMessage message={message} key={index}/>;
        });
        return (
            <div id ="rc-ontopic" className="flex-grow">
                { messages }
            </div>
        );
    }
}

OntopicContainer.propTypes = {
    messages: React.PropTypes.array.isRequired
};