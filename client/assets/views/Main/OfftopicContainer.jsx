import React from "react";
import PropTypes from "prop-types";
import classNames from "classnames";
import {inject, observer} from "mobx-react";
import stateStore from "../../stores/stateStore";

import OfftopicMessage from "./OfftopicMessage";


@inject("stateStore")
@observer
export default class OfftopicContainer extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        let messages = this.props.stateStore.offtopicMessages.map(function (message, index) {
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
};