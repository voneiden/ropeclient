import React from "react";
import classNames from "classnames";

function SumRolls(a, b) {
    if (Array.isArray(a)) {
        a = a.reduce(SumRolls, 0);
    }
    if (Array.isArray(b)) {
        b = b.reduce(SumRolls, 0);
    }
    return a+b;
}


export default class DiceRoll extends React.Component {
    constructor(props) {
        super(props);
        
    }


    render() {
        let data = JSON.parse(this.props.data);
        console.log("Data", data);
        let roll = data.roll;
        let results = data.results;
        let total = results.reduce(SumRolls, 0);
        let stringResults = results.toString().replace(/,/g, ", ");

        return (
            <span
                className="rc-dice-roll"
                onClick={this.toggleMode}
            >{roll}: {total} <span className="rc-dice-roll-results">{stringResults}</span></span>
        );
    }
}