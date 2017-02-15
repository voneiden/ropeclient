import React from "react";
import classNames from "classnames";


export default class ConfigView extends React.Component {
    constructor(props) {
        super(props);

        this.state = {};

    }

    render() {
        return (
            <div id="rc-configure" className="flex">
                <div className="mdl-color--purple-900">
                    <div className="flex-row rc-configure-align">
                        <span>Hellow</span>
                        <input></input>
                    </div>
                     <div className="flex-row rc-configure-align">
                        <span>asdfsadfsdafasdf asdf</span>
                        <input></input>
                    </div>
                    <br/>
                    <div className="flex-row rc-configure-align">
                        <button className="mdl-button mdl-js-button mdl-button--raised mdl-button--accent">
                            Cancel
                        </button>

                        <button className="mdl-button mdl-js-button mdl-button--raised mdl-button--colored">
                            Save
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}