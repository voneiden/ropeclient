import React from "react";
import classNames from "classnames";


export default class NameList extends React.Component {
    constructor(props) {
        super(props);

        this.state = {};

    }

    render() {
        console.log("Render player names", this.props.players);
        let namelist = [];
        let playerNames = Object.keys(this.props.players);
        for (let i=0; i < playerNames.length; i++) {
            let playerName = playerNames[i];
            let isTyping = this.props.players[playerName];
            namelist.push(
                <span key={playerName} className={classNames({
                    "is-typing": isTyping
                })}>{playerName}</span>
            );
        }

        return (
            <div id ="rc-namelist" className="">
                {namelist}
            </div>
        );
    }
}