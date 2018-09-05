import {observable, action} from "mobx";
export class StateStore {
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
}

const stateStore = new StateStore();
console.log("Statestore", stateStore);
export default stateStore;