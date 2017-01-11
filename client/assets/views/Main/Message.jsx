import React from "react";
import classNames from "classnames";
import DiceRoll from "./DiceRoll";

const PATTERN_DICE = /\$\{dice:(\{.+?})}/;


export default class Message extends React.Component {
    constructor(props) {
        super(props);
        this.state = {};

        this.replaceDiceRolls = this.replaceDiceRolls.bind(this);
    }


    replaceDiceRolls(text) {
        return text.split(PATTERN_DICE).map(function(value, index) {
            if (index % 2) {
                return <DiceRoll key={"roll-" + index-1} data={value}/>
            } else {
                return value;
            }
        }, this);
    }

    render() {
        return (
            <div className="rc-message">
                Message
            </div>
        );
    }
}


Message.propTypes = {

};