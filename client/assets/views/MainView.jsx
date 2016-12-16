import React from "react";
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
            <div id ="rc-main" className="flex flex-row">
                <div className="flex flex-column flex-grow">
                    <div className="flex-grow-2"><OfftopicContainer messages={this.props.offtopicMessages}/></div>
                    <div className="flex-grow-3"><OntopicContainer messages={this.props.ontopicMessages}/></div>
                    <Input
                        sendMessage={this.props.sendMessage}
                        sendIsTyping={this.props.sendIsTyping}
                        passwordMode={this.props.passwordMode}
                    />
                </div>
                <NameList/>
            </div>
        );
    }
}

MainView.propTypes = {
    offtopicMessages: React.PropTypes.array.isRequired,
    ontopicMessages: React.PropTypes.array.isRequired,
    sendMessage: React.PropTypes.array.isRequired,
    sendIsTyping: React.PropTypes.array.isRequired
};