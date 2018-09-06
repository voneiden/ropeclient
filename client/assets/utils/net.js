import stateStore from "../stores/stateStore";
import {action, autorun} from "mobx";

let websocket = null;
const defaultUrl = "ws://localhost:8090";


function onOpen(event) {
    console.info("Websocket open", event);
}

function onError(event) {
    console.error("Websocket error", event);
}

function onMessage(event) {
    console.info("Websocket message", event);
    try {
        return net.process(JSON.parse(event.data));
    }
    catch (ex) {
        console.error("Failed to parse data: " + event.data, ex);
        return false;
    }
}

export class Net {

    constructor() {
        autorun(() => {
            this.sendTyping(stateStore.isTyping);
        }, {delay: 10})
    }


    connect(url = defaultUrl) {
        if (websocket === null) {
            websocket = new WebSocket(url);
            websocket.onopen = onOpen;
            websocket.onmessage = onMessage;
            websocket.onerror = onError;
            return websocket;
        }
        return false;
    }

    sendText(text) {
        if (websocket) {
            let message = {
                k: "msg",
                v: text ? text : ""
            };
            console.log("Send", message);
            websocket.send(JSON.stringify(message));
        }
        if (stateStore.isPasswordMode) {
            stateStore.setPasswordMode(false);
        }
    }

    sendTyping(isTyping) {
        if (websocket) {
            let message = {
                k: isTyping ? "pit" : "pnt",
            };
            console.log("Send", message);
            websocket.send(JSON.stringify(message));
        }
    }

    @action
    process(dataset) {
        console.log("Process dataset", dataset);
        if (!Array.isArray(dataset)) {
            dataset = [dataset];
        }

        let clearOfftopic = false;
        let newOfftopicMessages = [];

        let clearOntopic = false;
        let newOntopicMessages = [];

        let passwordMode = false;

        for (let data of dataset) {
            if (!data.k) {
                console.warn("Invalid data, no key", data);
                continue;
            }

            switch (data.k) {
                case "oft":
                    console.log("Got oft message");
                    newOfftopicMessages.push(data);
                    break;
                case "ont":
                    console.log("Got ont message");
                    newOntopicMessages.push(data);
                    break;

                case "pwd":
                    console.log("Password passwordMode requested:", data);
                    stateStore.setPasswordMode(data);

                    break;
                case "clr":
                    switch (data.v) {
                        case "oft":
                            clearOfftopic = true;
                            newOfftopicMessages = [];
                            break;
                        case "ont":
                            clearOntopic = true;
                            newOntopicMessages = [];
                            break;
                        default:
                            clearOfftopic = clearOntopic = true;
                            newOfftopicMessages = [];
                            newOfftopicMessages = [];
                            break;
                    }
                    break;

                case "pll": {
                    console.log("Received player list", data);
                    let players = data.v.map((name) => ({name: name, typing: false}));
                    stateStore.replacePlayers(players);
                    break;
                }

                case "pit": {
                    console.log("Received player is typing", data);
                    stateStore.setPlayerTyping(data.a, true);
                    break;
                }

                case "pnt": {
                    console.log("Received player not typing", data);
                    stateStore.setPlayerTyping(data.a, false);
                    break;
                }

                default:
                    console.warn("Unknown data packet", data);
            }
        }

        if (newOfftopicMessages.length || clearOfftopic) {
            if (!clearOfftopic) {
                stateStore.offtopicMessages.push(...newOfftopicMessages);
            }
            else {
                stateStore.offtopicMessages.replace(newOfftopicMessages);
            }
        }

        if (newOntopicMessages.length || clearOntopic) {
            if (!clearOntopic) {
                stateStore.ontopicMessages.push(...newOntopicMessages);
            }
            else {
                stateStore.ontopicMessages.replace(newOntopicMessages);
            }
        }

        if (passwordMode) {
            stateStore.setPasswordMode(passwordMode);
        }
        console.log(stateStore);
    }
}

const net = new Net();
export default net;