import {observable, action, computed} from "mobx";
import {MODE} from "../utils/enums";

export class StateStore {
    /**
     *
     * @type {boolean|Object}
     * @property {String} ss
     * @property {String} ds
     */
    @observable passwordMode = false;
    @observable offtopicMessages = [];
    @observable ontopicMessages = [];
    @observable players = [];

    @action
    replacePlayers(players) {
        this.players.replace(players);
    }

    @action
    setPlayerTyping(name, typing) {
        let player = this.players.filter((player) => player.name === name);
        if (!player) {
            player = {name: name};
            this.players.push(name);
        }
        player[0].typing = typing;
        console.log(this.players);
    }

    @action
    setPasswordMode(passwordMode) {
        if (passwordMode) { this.passwordMode = passwordMode; }
        else { this.passwordMode = false; }
    }

    @computed
    get isPasswordMode() {
        return this.passwordMode;
    }
}


const stateStore = new StateStore();
console.log("Statestore", stateStore);
export default stateStore;