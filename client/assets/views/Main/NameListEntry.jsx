import React from "react";
import PropTypes from "prop-types";
import {observer} from "mobx-react";

@observer
export default class NameListEntry extends React.Component {
    render() {
        return (
            <div>
                {this.props.player.typing ? "*" : null}
                {this.props.player.name}
            </div>
        )
    }
}

NameListEntry.propTypes = {
    player: PropTypes.shape({
        name: PropTypes.string,
        typing: PropTypes.bool
    }),
};