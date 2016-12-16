import React from "react";
import classNames from "classnames";

import Offtopic from "./Main/OfftopicContainer";
import Ontopic from "./Main/OntopicContainer";
import Input from "./Main/Input";
import NameList from "./Main/NameList";

export default class MainView extends React.Component {
    constructor(props) {
        super(props);

        this.state = {};

    }

    render() {
        return (
            <div id ="rc-main" className="flex flex-row">
                <div className="flex flex-column flex-grow">
                    <div className="flex-grow-2"><OfftopicContainer messages={this.props.offtopicMessages}/></div>
                    <div className="flex-grow-3"><OntopicContainer messages={this.props.ontopicMessages}/></div>
                    <Input/>
                </div>
                <NameList/>
            </div>
        );
    }
}

MainView.propTypes = {
    offtopicMessages: React.PropTypes.array.isRequired,
    ontopicMessages: React.PropTypes.array.isRequired,
};