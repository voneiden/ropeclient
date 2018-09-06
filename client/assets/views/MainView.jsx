import React from "react";
import PropTypes from "prop-types";
import classNames from "classnames";

import OfftopicContainer from "./Main/OfftopicContainer";
import OntopicContainer from "./Main/OntopicContainer";
import Input from "./Main/Input";
import NameList from "./Main/NameList";

export default class MainView extends React.Component {
    constructor(props) {
        super(props);

        this.state = {};

    }

    render() {
        return (
            <div id="rc-main" className="flex flex-row">
                <div id="rc-main-bodytext" className="flex flex-column flex-grow">
                    <div className="flex-grow-2 flex-column"><OfftopicContainer messages={this.props.offtopicMessages}/></div>
                    <div className="flex-grow-3 flex-column"><OntopicContainer messages={this.props.ontopicMessages}/></div>
                    <Input/>
                </div>
                <NameList players={this.props.players}/>
            </div>
        );
    }
}

MainView.propTypes = {
    offtopicMessages: PropTypes.array.isRequired,
    ontopicMessages: PropTypes.array.isRequired,
    players: PropTypes.object.isRequired,
};