import React from "react";
import PropTypes from "prop-types";
import classNames from "classnames";
import {inject, observer} from "mobx-react";
import stateStore from "../../stores/stateStore";


import OntopicMessage from "./OntopicMessage";

@inject("stateStore")
@observer
export default class OntopicContainer extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        let messages = this.props.stateStore.ontopicMessages.map(function (message, index) {
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
};