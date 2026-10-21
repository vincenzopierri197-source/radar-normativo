// Stampa il JSON dei comandi per setMyCommands.
import { BOT_COMMANDS } from "./index.js";
console.log(JSON.stringify(BOT_COMMANDS.map(([command, description]) => ({ command, description }))));
