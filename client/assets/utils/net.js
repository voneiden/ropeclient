import stateStore from "../stores/stateStore";

let websocket = null;
const defaultUrl = "ws://localhost:8090";


function onOpen(event) {
    console.info("Websocket open", event);
}

function onError(event) {
    console.error("Websocket error", event);
}

function onMessage() {
    try {
        return this.process(JSON.parse(event.data));
    }
    catch (ex) {
        console.error("Failed to parse data: " + event.data, ex);
        return false;
    }
}

export default class Net {
    static connect(url=defaultUrl) {
        if (websocket === null) {
            websocket = new WebSocket(url);
            websocket.onopen = onOpen;
            websocket.onmessage = onMessage;
            websocket.onerror = onError;
            return websocket;
        }
        return false;
    }
}

function process(dataset) {
    if (!Array.isArray(dataset)) {
        dataset = [dataset];
    }
    let clearOfftopic = false;
    let offtopicMessages = [];

    let clearOntopic = false;
    let ontopicMessages = [];

    let state = {
        passwordMode: false
    };

    for (let data of dataset) {
        if (!data.k) {
            console.warn("Invalid data, no key", data);
            return false;
        }

        switch (data.k) {
            case "oft":
                offtopicMessages.push(data);
                break;
            case "ont":
                console.log("Got ont message");
                ontopicMessages.push(data);
                break;

            case "pwd":
                console.log("Password mode requested:", data);
                state.passwordMode = data;

                break;
            case "clr":
                switch (data.v) {
                    case "oft":
                        clearOfftopic = true;
                        offtopicMessages = [];
                        break;
                    case "ont":
                        clearOntopic = true;
                        ontopicMessages = [];
                        break;
                    default:
                        clearOfftopic = clearOntopic = true;
                        offtopicMessages = [];
                        offtopicMessages = [];
                        break;
                }
                break;

            case "pll": {
                console.log("Received player list", data);
                let players = data.v.map((name) => ({name: name, typing: false}));
                this.props.stateStore.replacePlayers(players);
                break;
            }

            case "pit": {
                console.log("Received player is typing", data);
                this.props.stateStore.setPlayerTyping(data.a, true);
                break;
            }

            case "pnt": {
                console.log("Received player not typing", data);
                this.props.stateStore.setPlayerTyping(data.a, false);
                break;
            }

            default:
                console.warn("Unknown data packet", data);
        }
    }

    if (offtopicMessages.length || clearOfftopic) {
        state.offtopicMessages = clearOfftopic ? offtopicMessages : this.state.offtopicMessages.concat(offtopicMessages);
    }

    if (ontopicMessages.length || clearOntopic) {
        state.ontopicMessages = clearOntopic ? ontopicMessages : this.state.ontopicMessages.concat(ontopicMessages);
    }

    this.setState(state);
}