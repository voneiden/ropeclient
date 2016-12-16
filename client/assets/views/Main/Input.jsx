import React from "react";
import classNames from "classnames";


export default class Input extends React.Component {
    constructor(props) {
        super(props);

        this.state = {};

    }

    render() {
        return (
            <div id ="rc-input" className="flex flex-row">
                <textarea className="flex-grow"></textarea>
            </div>
        );
    }
}