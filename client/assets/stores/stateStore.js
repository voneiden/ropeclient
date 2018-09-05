import {observable, action, computed} from "mobx";
import {MODE} from "../utils/enums";

export class StateStore {
    @observable mode = MODE.NORMAL;
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

    @computed
    get isPasswordMode() {
        return this.mode === MODE.PASSWORD;
    }
}


const stateStore = new StateStore();
console.log("Statestore", stateStore);
export default stateStore;