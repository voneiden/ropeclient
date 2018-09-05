import React from "react";
import PropTypes from "prop-types";
import classNames from "classnames";
import NameListEntry from "./NameListEntry";
import {inject, observer} from "mobx-react";
import {StateStore} from '../../stores/stateStore';

@inject("stateStore")
@observer
export default class NameList extends React.Component {
    constructor(props) {
        super(props);
    }

    render() {
        console.log("This", this.props.store);
        return (
            <div id="rc-namelist">
                { this.props.stateStore.players.map((player) => <NameListEntry player={player} key={player}/>) }
            </div>
        );
    }
}

StateStore.propTypes = {
    stateStore: PropTypes.instanceOf(StateStore)
}